from pydrive.auth import GoogleAuth
import yaml


class GoogleAuthentication(object):

    @staticmethod
    def get_auth_token():
        """
        Get authentication token for Google Drive.
        Creates, refreshes, and/or stores related credentials.

        :rtype: GoogleAuth
        """
        g_auth = GoogleAuth()
        config = yaml.safe_load(open("conf/.config.yml"))
        credentials = config['google_drive']['cached_token_filename']
        g_auth.LoadCredentialsFile(credentials)
        if g_auth.credentials is None:
            # Authenticate via browser if credentials are not set
            g_auth.LocalWebserverAuth()
        elif g_auth.access_token_expired:
            # Refresh credentials if expired
            g_auth.Refresh()
        else:
            # Initialize the saved credentials
            g_auth.Authorize()

        g_auth.SaveCredentialsFile(credentials)
        return g_auth

    @staticmethod
    def upload_file(filename, path=None):
        """
        Uploads file to Google Drive based on supplied path + filename

        :type filename: str
        :type path: str
        """
        path_filename = filename
        if path is not None:
            path_filename = '{}/{}'.format(path, filename)

        count = 0
        while True:
            try:
                g_auth = GoogleAuthentication.get_auth_token()
                upload_request = g_auth.service.files().insert(media_body=path_filename,
                                                               body={'title': filename,
                                                                     'convert': True})
                break
            except AttributeError as message:
                if count > 5:
                    raise AttributeError(message)
                count += 1

        upload_request.execute()
