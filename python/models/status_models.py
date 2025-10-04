"""
Status tracking models for scraping operations
"""

# Store scraping status
scraping_status = {
    'is_running': False,
    'progress': 0,
    'total': 0,
    'current_company': '',
    'results': []
}

validation_status = {
    'is_running': False,
    'progress': 0,
    'total': 0,
    'current_company': '',
    'validated_count': 0,
    'removed_count': 0
}

agent_status = {
    'is_running': False,
    'progress': 0,
    'total': 0,
    'current_company': ''
}
