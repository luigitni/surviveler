#include "strutils.h"
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>

char*
string_fmt(const char *fmt, ...)
{
	va_list ap, ap_copy;
	va_start(ap, fmt);

	va_copy(ap_copy, ap);
	size_t msg_len = vsnprintf(NULL, 0, fmt, ap_copy) + 1;
	va_end(ap_copy);

	char *msg = malloc(msg_len);
	if (msg) {
		va_copy(ap_copy, ap);
		vsnprintf(msg, msg_len, fmt, ap_copy);
		va_end(ap_copy);
	}
	va_end(ap);
	return msg;
}
