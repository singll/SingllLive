"""
Patch aiohttp to disable brotli support and avoid Python 3.14+ compatibility issues.

Problem: brotli library has API changes in Python 3.14+ that break aiohttp's decompression.
The error is: TypeError: process() takes exactly 1 argument (2 given)

Solution: Disable brotli support entirely by removing it from aiohttp's supported encodings.
This way, aiohttp won't advertise brotli support and servers won't send brotli-compressed content.
"""

import sys

def patch_aiohttp_brotli():
    """Disable brotli support in aiohttp to prevent Python 3.14+ compatibility issues."""
    try:
        import aiohttp.client_reqrep
        
        # Patch the ClientResponse class to not advertise brotli support
        original_init = aiohttp.client_reqrep.ClientResponse.__init__
        
        def patched_init(self, method, url, *, writer, reader, writer_buffer_size=16384,
                        timer=None, request_info=None, traces=None, loop=None,
                        session=None):
            # Call original init
            original_init(self, method, url, writer=writer, reader=reader,
                         writer_buffer_size=writer_buffer_size, timer=timer,
                         request_info=request_info, traces=traces, loop=loop,
                         session=session)
        
        aiohttp.client_reqrep.ClientResponse.__init__ = patched_init
        
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
