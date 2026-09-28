"""
Version information for the Active Friends Club application
"""
import os
from datetime import datetime

# Version information
VERSION_MAJOR = 2
VERSION_MINOR = 2
VERSION_PATCH = 0
VERSION_BUILD = os.getenv('BUILD_NUMBER', 'dev')

# Build information
BUILD_DATE = os.getenv('BUILD_DATE', datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'))
BUILD_COMMIT = os.getenv('BUILD_COMMIT', 'unknown')
BUILD_BRANCH = os.getenv('BUILD_BRANCH', 'development')

def get_version_string():
    """Get the full version string"""
    if VERSION_BUILD == 'dev':
        return f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}-dev"
    else:
        return f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}.{VERSION_BUILD}"

def get_short_version():
    """Get the short version for display in navbar"""
    return f"{VERSION_MAJOR}.{VERSION_MINOR}"

def get_version_info():
    """Get comprehensive version information"""
    return {
        'version': get_version_string(),
        'short_version': get_short_version(),
        'major': VERSION_MAJOR,
        'minor': VERSION_MINOR,
        'patch': VERSION_PATCH,
        'build': VERSION_BUILD,
        'build_date': BUILD_DATE,
        'build_commit': BUILD_COMMIT,
        'build_branch': BUILD_BRANCH,
        'is_development': VERSION_BUILD == 'dev'
    }