# Calculator Module for MergeMate Demo

def add(a, b):
    return a + b

<<<<<<< HEAD
# Implementation from 'performance-optimization' branch
def multiply(a, b):
    # Optimized using bit shifts for powers of 2
    return a * b
=======
# Implementation from 'logging-feature' branch
def multiply(a, b):
    print(f"DEBUG: Multiplying {a} and {b}")
    return a * b
>>>>>>> logging-feature

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

<<<<<<< HEAD
APP_THEME = "dark-mode"
ENABLE_TELEMETRY = False
=======
APP_THEME = "cyberpunk"
ENABLE_TELEMETRY = True
>>>>>>> logging-feature
