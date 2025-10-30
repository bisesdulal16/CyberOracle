"""
DLP (Data Loss Prevention) Middleware
-------------------------------------
Purpose:
Intercepts incoming POST, PUT, and PATCH requests and scans them for
sensitive data such as SSNs, credit card numbers, emails, or API keys.
If detected, the values are redacted ("***") before the data reaches the
main application or database layer.

This ensures sensitive information is never logged, stored, or leaked.
"""

import re    #Python regex library
from starlette.middleware.base import BaseHTTPMiddleware #Base class that lets to create custom middleware in FastAPI/Starlette
from starlette.requests import Request  #Represents an incoming HTTP request object
from starlette.responses import JSONResponse #useful to block requests

# Dictionary of regex patterns that match sensitive data formats
SENSITIVE_PATTERNS = {
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",            #matches a US Social Security Number format 
    "credit_card": r"\b(?:\d[ -]*?){13,16}\b",  #matches 13-16 digit credit card numbers with or without spaces/dashes
    "email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", #matches email address formats
    "api_key": r"\b[A-Za-z0-9]{32,}\b",         #matches (32+ chars) long alphanumeric strings often used as access keys or tokens
}


class DLPFilterMiddleware(BaseHTTPMiddleware):
    """
    Custom FastAPI middleware that scans and redacts sensitive data from 
    incoming request bodies before they are processed by router handlers.
    """
    async def dispatch(self, request: Request, call_next):
        #target only data-carrying methods
        if request.method in{"POST", "PUT", "PATCH"}:
            
            #try to read the JSON body of the request if empty or invalid fallback to an empty dictionary
            try:
                body = await request.json()
            except Exception:
                body = {}
            
            #set redacted to false to track changes made
            redacted = False
            
            #loop through every key-value pair in the JSON
            for key, value in body.items():
                #if the value is a string 
                if isinstance(value, str):
                    #loop through each pattern in SENSITIVE_PATTERNS
                    for name, pattern in SENSITIVE_PATTERNS.items():
                        #if the regex finds a match (re.search), replace it with "***" using re.sub
                        if re.search(pattern, value):
                            body[key] = re.sub(pattern, "***", value)
                            #mark the request as redacted
                            redacted = True
            
            #if any sensitive data was found and replaced convert the cleaned body back into bytes and replace original raw request body
            #ensures downstream route handlers receive the sanitized version.
            if redacted:
                request._body = str.encode(str(body))
        
        #once processing is done, the sanitized request is forwarded to the next layer (FastAPI route.)        
        response = await call_next(request)
        return response
