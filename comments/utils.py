import os


def validate_file_extention(value, allowed_extentions):
    '''Check if a filefield (value) has allowed extentions.'''
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    return ext.lower() in allowed_extentions
