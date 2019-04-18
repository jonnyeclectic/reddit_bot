"""RedditBot class for gathering and using Reddit data."""
from FileHelper import FileHelper
from praw import Reddit
from praw.models import MoreComments


class RedditBot(FileHelper):

    def __init__(self):
        super(RedditBot, self).__init__()
        self.reddit_client = self.get_reddit_client()
        self.comment_types = self.config['comments']['sorting_types']
        self.subreddits = self.config['subreddits']['subreddit_titles']
        self.subreddit_posts = None
        self.sorted_comments = None
        self.post_limit = self.config['posts']['post_limit']

    def get_reddit_client(self):
        """
        Gets client for Reddit.

        :rtype: Reddit
        """

        return Reddit(
            client_id=self.config['reddit_bot']['client_id'],
            client_secret=self.config['reddit_bot']['client_secret'],
            user_agent=self.config['reddit_bot']['user_agent'],
            username=self.config['reddit_bot']['username'],
            password=self.config['reddit_bot']['password'])

    def prepare_post(self, post):
        """
        Prepares comment filters and options.
        Also writes post to file before grabbing comments.

        :type post: Submission
        :rtype: Submission
        """
        post.comment_sort = self.config['comments']['sort_by']
        post.comment_limit = self.config['comments']['comment_limit']
        self.store_post(post)
        return post

    def get_all_comments(self, post):
        """
        Fetches comments for all depths and flattens them.

        :type post: Submission
        """
        count = 0
        while True:
            try:
                post.comments.replace_more(limit=None)
                comments = post.comments.list()
                break
            except Exception as message:
                if count > 5:
                    raise Exception(message)
                count += 1
                pass

        scored_comments = {}
        for comment in comments:
            if isinstance(comment, MoreComments) \
                    or (
                    comment.score < self.config['comments']['score_threshold']
                    and not comment.distinguished
            ):
                continue

            while comment.score in scored_comments.keys():
                comment.score += 1
            scored_comments.update({comment.score: comment})

        sorted(scored_comments.keys(), reverse=True)

        from collections import OrderedDict
        self.sorted_comments = OrderedDict(scored_comments)

    def process_popular_activity(self):
        """
        Fetches all comments in subreddit posts and stores them based on configs.
        """
        self.update_filename_with_timestamp('text_file')
        self.store_intro()
        post_counter = 0
        for post in self.subreddit_posts:
            post = self.prepare_post(post=post)
            self.get_all_comments(post)

            comment_counter = 0
            for sorted_comment in self.sorted_comments.values():
                if comment_counter >= self.config['comments']['comment_limit']:
                    break
                comment_counter += 1
                self.store_comment(sorted_comment)
            self.store_segue()
            post_counter += 1

    def get_comment_audio(self):
        """
        Creates and uploads audio files of Reddit posts and comments.
        """
        for subreddit in self.subreddits:
            self.subreddit_posts = self.reddit_client.subreddit(subreddit).top(
                time_filter=self.config['posts']['time_filter'],
                limit=self.config['posts']['post_limit'])
            self.process_popular_activity()
        self.store_outro()
        self.text_to_speech()
        self.upload_speech()

    def store_intro(self):
        """
        Writes intro for the file about the subreddits.
        """
        content = "Here's what's happening with "
        content = self.get_human_readable_subreddit_list(content)
        content += "\nLet's get started."
        self.store(content)

    def store_outro(self):
        """
        Writes intro for the file about the subreddits and comments.
        """
        content = '\nThat concludes our look at '
        content = self.get_human_readable_subreddit_list(content)
        content += '\nSmash that like button for less anxiety.'
        self.store(content)

    def get_human_readable_subreddit_list(self, content):
        """
        Get grammatically correct list of subreddits for dictation.

        :param content: str
        :return: str
        """
        for count, subreddit in enumerate(self.subreddits):
            if len(self.subreddits) == 1:
                content += 'r/{}.'.format(subreddit)
            elif len(self.subreddits) == 2:
                if count + 1 == len(self.subreddits):
                    content += 'and r/{}.'.format(subreddit)
                else:
                    content += 'r/{} '.format(subreddit)
            else:
                if count + 1 == len(self.subreddits):
                    content += 'and r/{}.'.format(subreddit)
                else:
                    content += 'r/{}, '.format(subreddit)
        return content

    def store_segue(self):
        """
        Writes segue to next post to file.
        """
        self.store("\n Hmmm...kay\n")

    def store_post(self, post):
        """
        Writes subreddit post data to file.

        :type post: Submission
        """
        self.store('\n***{}***\n {}\n\n'.format(post.title, post.selftext))
        self.store('[[{} - {}]]'.format(post.author, post.score), False)
        self.store(FileHelper.get_dictation_pause(), False)

    def store_comment(self, comment):
        """
        Writes comment data from subreddit post to file.

        :type comment: Comment
        """
        self.store('\n* {}\n'.format(comment.body))
        self.store('[[{} - {}]]'.format(comment.author, comment.score), False)
        self.store(FileHelper.get_dictation_pause(1000), False)


bot = RedditBot()
bot.get_comment_audio()
