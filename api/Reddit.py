"""RedditBot class for gathering and using Reddit data."""
from FileHelper import FileHelper
from praw import Reddit
from praw.models import MoreComments


class RedditBot(FileHelper):
    # Number of comments per post
    COMMENT_LIMIT = 8
    # Minimum comment upvotes required
    SCORE_THRESHOLD = 200

    def __init__(self):
        self.reddit_client = self.get_reddit_client()
        self.comment_types = self.get_comment_types()
        self.subreddits = self.get_subreddits()
        self.comment_options = RedditBot.get_comment_options()
        self.subreddit_posts = None
        self.sorted_comments = None
        self.post_limit = 4

        super(RedditBot, self).__init__()

    @staticmethod
    def get_reddit_client():
        """
        Gets client for Reddit.

        :rtype: Reddit
        """
        pass

        # return Reddit(
        #     client_id=client_id,
        #     client_secret=client_secret,
        #     user_agent=user_agent,
        #     username=username,
        #     password=password)

    @staticmethod
    def get_comment_types():
        """
        Gets sorting types for comments.

        :rtype: list
        """
        return [
            'controversial',
            'gilded',
            'hot',
            'new',
            'rising',
            'top'
        ]

    @staticmethod
    def get_subreddits():
        """
        Gets subreddits.

        :rtype: list
        """
        return [
            # 'askReddit',
            'jokes'
        ]

    @staticmethod
    def get_comment_options():
        """
        Gets sorting and filter options for comments.

        :rtype: dict
        """
        return {
            'sort_by': 'top',
            'limit': RedditBot.COMMENT_LIMIT
        }

    def prepare_post(self, post):
        """
        Prepares comment filters and options.
        Also writes post to file before grabbing comments.

        :type post: Submission
        :rtype: Submission
        """
        post.comment_sort = self.comment_options.get('sort_by')
        post.comment_limit = self.comment_options.get('limit')
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
                    comment.score < self.SCORE_THRESHOLD
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
                if comment_counter >= RedditBot.COMMENT_LIMIT:
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
            self.subreddit_posts = self.reddit_client.subreddit(subreddit).top(time_filter='day',
                                                                               limit=self.post_limit)
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

    def store_comment(self, comment):
        """
        Writes comment data from subreddit post to file.

        :type comment: Comment
        """
        self.store('\n* {}\n'.format(comment.body))
        self.store('[[{} - {}]]'.format(comment.author, comment.score), False)
        self.store(FileHelper.get_dictation_pause(), False)


bot = RedditBot()
bot.get_comment_audio()

