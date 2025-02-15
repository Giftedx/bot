import win32evtlog
import win32evtlogutil

try:
    message = "Bot test script executed"
    win32evtlogutil.ReportEvent(
        "Bot Test Script",  # App name
        1,                  # Event ID
        eventType=win32evtlog.EVENTLOG_INFORMATION_TYPE,
        strings=[message]
    )
    # Also try writing to a file in the Windows temp directory
    import tempfile
    import os
    temp_file = os.path.join(tempfile.gettempdir(), 'bot_test.txt')
    with open(temp_file, 'w') as f:
        f.write("Bot test successful")
    print(f"Test file written to: {temp_file}")
    
except Exception as e:
    # If all else fails, create a .error file
    with open('bot_test.error', 'w') as f:
        f.write(f"Error: {str(e)}")

