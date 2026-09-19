# Additional probe receipt (not used as qualification)

At 2026-09-12T17:13:48+08:00, a second header-only curl probe was attempted after the already completed 512-byte prefix retrieval. It ended with `curl (35) LibreSSL SSL_ERROR_SYSCALL` and wrote zero bytes to `zip_prefix_headers.txt`. No dataset body was changed or downloaded. This is retained as a transport failure record; the successful prefix and tail probes remain the qualification evidence.
