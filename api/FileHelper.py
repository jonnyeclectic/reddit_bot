from auth.GoogleAuthentication import GoogleAuthentication

import datetime
import os
import shutil
import yaml


class FileHelper:

    def __init__(self):
        self.config = yaml.safe_load(open("conf/.config.yml"))
        self.text_file = self.config['files']['text_filename']
        self.mp4_file = self.config['files']['audio_filename']
        self.logs_file = self.config['files']['logs_filename']
        self.timestamp = None

    def remove_file(self, file):
        """
        Removes file.
        """
        self.bot_log('Removing file: {}.'.format(file))
        filename = '{}/{}'.format(self.config['files']['directory'], file)
        if os.path.isfile(filename):
            os.remove(filename)

    def text_to_speech(self):
        """
        Creates text to speech audio file from subreddit and comments file.
        """
        self.bot_log('Converting text to speech.')
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

    def bot_log(self, content):
        """
        Write content to log file.

        :param content: str
        """
        filename = '{}/{}'.format(self.config['files']['directory'], self.logs_file)
        with open(filename, "a+") as f:
            f.write('{}\n'.format(content))
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

        content = re.sub('\\(*.http.*?\\)', ' ', content, flags=re.IGNORECASE)
        content = re.sub(' *.http.*? ', ' ', content, flags=re.IGNORECASE)
        content = re.sub('fuck', 'fcuk', content, flags=re.IGNORECASE)
        content = re.sub('shit', 'shiz', content, flags=re.IGNORECASE)
        content = re.sub('bitch', 'beach', content, flags=re.IGNORECASE)
        content = re.sub('sex', 'six', content, flags=re.IGNORECASE)
        content = re.sub(' *.com.*? ', ' ', content, flags=re.IGNORECASE)
        content = re.sub('\\[.*.\\]', ' ', content, flags=re.IGNORECASE)

        if 'I am a bot' in content:
            return ''
        if len(re.sub(' ', '', content)) <= 5:
            return ''

        return content

    def upload_speech(self):
        """
         Uploads text to speech audio file to Google Drive
         """
        self.bot_log('Uploading speech.')
        if os.path.isfile(self.text_file):
            GoogleAuthentication.upload_file(self.text_file, self.config['files']['directory'])
            self.remove_file(self.text_file)
        if os.path.isfile(self.mp4_file):
            GoogleAuthentication.upload_file(self.mp4_file, self.config['files']['directory'])
            self.remove_file(self.mp4_file)

    def update_filenames_with_timestamp(self):
        """
         Updates filenames with timestamp.
         """
        for filename_variable in ['text_file', 'mp4_file', 'logs_file']:
            filename = getattr(self, filename_variable)
            self.timestamp = datetime.datetime.now().strftime("%I:%M%p")
            updated_filename = "{}_{}".format(self.timestamp, filename)
            setattr(self, filename_variable, updated_filename)
