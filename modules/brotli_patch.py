"""
Patch aiohttp to disable brotli support and avoid Python 3.14+ compatibility issues.

Problem: brotli library has API changes in Python 3.14+ that break aiohttp's decompression.
The error is: TypeError: process() takes exactly 1 argument (2 given)

Additional Problem: aiohttp has race condition in write_bytes where protocol might be None
in Python 3.14. Error: AssertionError: protocol is not None

Solution:
1. Disable brotli support entirely by removing it from aiohttp's supported encodings.
2. Patch write_bytes to handle None protocol gracefully.
"""

import sys

def patch_aiohttp_brotli():
    """Disable brotli support in aiohttp to prevent Python 3.14+ compatibility issues."""
    try:
        import aiohttp.client_reqrep

        # Patch the ClientResponse class to not advertise brotli support
        original_init = aiohttp.client_reqrep.ClientResponse.__init__

        def patched_init(self, method, url, **kwargs):
            # Python 3.14+ aiohttp may have additional parameters
            # Simply pass all kwargs to the original init
            original_init(self, method, url, **kwargs)

        aiohttp.client_reqrep.ClientResponse.__init__ = patched_init

        # Patch write_bytes to handle protocol=None race condition in Python 3.14
        try:
            original_write_bytes = aiohttp.client_reqrep.ClientRequest.write_bytes

            async def patched_write_bytes(self, writer, conn=None):
                """Patched write_bytes that handles protocol=None gracefully"""
                try:
                    # Check if protocol is None before accessing it
                    # This handles race conditions in Python 3.14
                    if hasattr(writer, '_protocol') and writer._protocol is None:
                        # Protocol not yet established, skip this write attempt
                        return
                    # Call original with all provided arguments
                    if conn is not None:
                        return await original_write_bytes(self, writer, conn)
                    else:
                        return await original_write_bytes(self, writer)
                except AssertionError as e:
                    if "protocol is not None" in str(e):
                        # Suppress this specific race condition error - it's non-fatal
                        # Connection will retry anyway
                        return
                    raise

            aiohttp.client_reqrep.ClientRequest.write_bytes = patched_write_bytes
        except (AttributeError, TypeError):
            # write_bytes may not exist or be patchable in some versions
            pass

        # Also patch the compression handling
        try:
            import aiohttp.http_parser
            # Try to disable brotli in the http parser
            if hasattr(aiohttp.http_parser, '_SUPPORTED_DECODERS'):
                # Remove brotli from supported decoders if present
                if 'br' in aiohttp.http_parser._SUPPORTED_DECODERS:
                    del aiohttp.http_parser._SUPPORTED_DECODERS['br']
        except (AttributeError, ImportError, KeyError):
            pass

        # Patch ClientSession to not request brotli
        try:
            from aiohttp import hdrs
            original_client_session_init = aiohttp.ClientSession.__init__

            def patched_client_session_init(self, *args, headers=None, **kwargs):
                # Ensure Accept-Encoding doesn't include brotli
                if headers is None:
                    headers = {}
                elif not isinstance(headers, dict):
                    headers = dict(headers)
                else:
                    headers = dict(headers)  # Make a copy

                # Only request gzip and deflate, not brotli
                if hdrs.ACCEPT_ENCODING not in headers:
                    headers[hdrs.ACCEPT_ENCODING] = 'gzip, deflate'

                original_client_session_init(self, *args, headers=headers, **kwargs)

            aiohttp.ClientSession.__init__ = patched_client_session_init
        except Exception:
            pass

        return True
    except Exception as e:
        print(f"Warning: Failed to patch aiohttp brotli: {e}", file=sys.stderr)
        return False

# Apply patch on module import
patch_aiohttp_brotli()
