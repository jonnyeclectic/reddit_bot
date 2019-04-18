from auth.GoogleAuthentication import GoogleAuthentication

import datetime
import os
import shutil
import yaml


class FileHelper:

    def __init__(self):
        self.config = yaml.safe_load(open("../.config.yml"))
        self.text_file = self.config['files']['text_filename']
        self.mp4_file = self.config['files']['audio_filename']

    def remove_file(self, file):
        """
        Removes file.
        """
        filename = '{}/{}'.format(self.config['files']['directory'], file)
        if os.path.isfile(filename):
            os.remove(filename)

    def text_to_speech(self):
        """
        Creates text to speech audio file from subreddit and comments file.
        """
        self.update_filename_with_timestamp('mp4_file')
        command = 'say'
        if shutil.which(command) is not None:
            os.system('{} -o {}/{} -f {}/{}'.format(command,
                                                    self.config['files']['directory'],
                                                    self.mp4_file,
                                                    self.config['files']['directory'],
                                                    self.text_file))

    @staticmethod
    def get_dictation_pause(duration=650):
        """
        Get command to make bot pause during dictation for the length of duration.

        :param duration: int
        :return: str
        """
        return '[[slnc {}]]'.format(duration)

    def store(self, content, clean_flag=True):
        """
        Write content to file.

        :param content: str
        :param clean_flag: bool
        """
        filename = '{}/{}'.format(self.config['files']['directory'], self.text_file)
        if clean_flag:
            content = self.clean(content)
        with open(filename, "a+") as f:
            f.write(content)
            f.close()

    @staticmethod
    def clean(content):
        """
        Clean text by parsing for anything flagged for removal.

        :param content: str
        :return: str
        """
        content += ' '
        import re
        # @TODO: Parse out any other rules in post

        content = re.sub('\\(*.http.*?\\)', ' ', content)
        content = re.sub(' *.http.*? ', ' ', content)
        content = re.sub('fuck', 'fcuk', content)
        content = re.sub('shit', 'shiz', content)
        content = re.sub('bitch', 'beach', content)
        content = re.sub('sex', 'six', content)
        content = re.sub(' *.com.*? ', ' ', content)
        content = re.sub('\\[.*.\\]', ' ', content)

        if 'I am a bot' in content:
            return ''
        if len(re.sub(' ', '', content)) <= 5:
            return ''

        return content

    def upload_speech(self):
        """
         Uploads text to speech audio file to Google Drive
         """
        GoogleAuthentication.upload_file(self.text_file, self.config['files']['directory'])
        GoogleAuthentication.upload_file(self.mp4_file, self.config['files']['directory'])
        self.remove_file(self.text_file)
        self.remove_file(self.mp4_file)

    def update_filename_with_timestamp(self, filename_variable):
        """
         Updates filename with timestamp.

         :param filename_variable: str
         """
        filename = getattr(self, filename_variable)
        timestamp = datetime.datetime.now().strftime("%I:%M%p")
        updated_filename = "{}_{}".format(timestamp, filename)
        setattr(self, filename_variable, updated_filename)
