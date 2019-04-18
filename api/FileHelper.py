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
        self.destination = self.config['destination']
        self.timestamp = None

        self.update_filenames_with_timestamp()

    def remove_file(self, filename):
        """
        Removes file.

        :param filename: str
        """
        self.bot_log('Removing file: {}.'.format(filename))
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
                                                    self.destination,
                                                    self.mp4_file,
                                                    self.destination,
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
        filename = '{}/{}'.format(self.destination, self.text_file)
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
        filename = '{}/{}'.format(self.destination, self.logs_file)
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
        self.bot_log('Attempting to upload speech.')
        text_file = '{}/{}'.format(self.destination, self.text_file)
        mp4_file = '{}/{}'.format(self.destination, self.mp4_file)
        if os.path.isfile(text_file):
            self.bot_log('Uploading speech script.')
            result = GoogleAuthentication.upload_file(text_file)
            if not result:
                self.bot_log('Failed uploading speech script.')
            self.remove_file(text_file)

        if os.path.isfile(mp4_file):
            self.bot_log('Uploading speech audio.')
            result = GoogleAuthentication.upload_file(mp4_file)
            if not result:
                self.bot_log('Failed uploading speech audio.')
            self.remove_file(mp4_file)

    def update_filenames_with_timestamp(self):
        """
         Updates filenames with timestamp.
         """
        self.timestamp = datetime.datetime.now().strftime("%I:%M%p")
        for filename_variable in ['text_file', 'mp4_file', 'logs_file']:
            filename = getattr(self, filename_variable)
            updated_filename = "{}_{}".format(self.timestamp, filename)
            setattr(self, filename_variable, updated_filename)
