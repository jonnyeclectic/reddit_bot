"""RedditBot class for gathering and using Reddit data."""
import time
from collections import OrderedDict
from FileHelper import FileHelper
from praw import Reddit
from praw.models import MoreComments


class RedditBot(FileHelper):

    def __init__(self):
        self.get_values_from_configs()
        self.subreddit_posts = []
        self.top_content_tree = {}

        self.reddit_client = self.get_reddit_client()
        super(RedditBot, self).__init__()

    def get_values_from_configs(self):
        """
        Get config values pertaining to Reddit.
        """
        super(RedditBot, self).get_values_from_configs()
        self.comment_options = self.config['comments']
        self.post_options = self.config['posts']
        self.subreddits = self.config['subreddits']['subreddit_titles']
        self.post_limit = self.config['posts']['post_limit']
        self.reddit_bot = self.config['reddit_bot']

    def get_reddit_client(self):
        """
        Gets client for Reddit.

        :rtype: Reddit
        """
        return Reddit(
            client_id=self.reddit_bot['client_id'],
            client_secret=self.reddit_bot['client_secret'],
            user_agent=self.reddit_bot['user_agent'],
            username=self.reddit_bot['username'],
            password=self.reddit_bot['password'])

    def prepare_post(self, post):
        """
        Prepares comment filters and options.

        :type post: Submission
        :rtype: Submission
        """
        post.comment_sort = self.comment_options['sort_by']
        post.comment_limit = self.comment_options['comment_limit']
        return post

    def get_qualified_comments(self, post):
        """
        Fetches comments for all depths, evaluates, and truncates them.

        :type post: Submission
        :rtype: Comment[]
        """
        self.bot_log('Getting all comments.')

        post = self.prepare_post(post=post)
        count = 0
        while True:
            try:
                post.comments.replace_more(limit=None)
                comments = post.comments.list()
                self.bot_log('Finished getting {} comments.'.format(len(comments)))
                break
            except Exception as message:
                self.bot_log('Error getting all comments.')
                if count > 5:
                    raise Exception(message)
                count += 1

        top_comments = self.get_top_comments(comments)
        top_sorted_comments = self.get_sorted_comments(top_comments)
        truncated_top_sorted_comments = self.get_truncated_comments(top_sorted_comments)

        self.bot_log('Finished getting, storing, and sorting comments.')
        return truncated_top_sorted_comments

    def get_top_comments(self, comments):
        """
        Evaluates all comments and returns a subset that qualifies per config criteria.

        :type comments: Comment[]
        :rtype: Comment[]
        """
        self.bot_log('Evaluating comments.')

        # In case none of the comments qualify per configs, grab the top rated comment (however low it may be).
        backup_comment = None

        top_comments = {}
        for comment in comments:
            if isinstance(comment, MoreComments) or len(comment.body) < 2:
                continue

            if comment.score < self.comment_options['score_threshold']:
                self.bot_log('Skipping low scored comment: {}.'.format(comment.score))
                if backup_comment is None or backup_comment.score < comment.score:
                    backup_comment = comment
                continue

            while comment.score in top_comments.keys():
                self.bot_log('Breaking tie for comment score: {}'.format(comment.score))
                comment.score += 1

            self.bot_log('Saving qualified comment: {}'.format(comment.body))
            top_comments.update({comment.score: comment})

        if len(top_comments) == 0:
            top_comments.update({backup_comment.score: backup_comment})

        return top_comments

    def get_sorted_comments(self, comments):
        """
        Converts comments to a top rated, sorted OrderedDict.

        :type comments: Comment[]
        :rtype: o{int: Comment}
        """
        sorted_comments = OrderedDict()
        for score in sorted(comments, reverse=True):
            sorted_comments.update({score: comments[score]})
        
        return sorted_comments

    def get_post_qualified_comments(self):
        """
        Fetches all comments in subreddit posts and stores them based on configs.

        :rtype: {Submission: Comment[]}
        """
        self.bot_log('Iterating posts.')

        post_qualified_comments = {}
        for post in self.subreddit_posts:
            qualified_comments = self.get_qualified_comments(post)
            post_qualified_comments.update({post: qualified_comments})
        return post_qualified_comments

    def get_truncated_comments(self, comments):
        """
        Parse sorted comments and return top content based on criteria.

        :type comments: Comment[]
        :rtype: Comment[]
        """
        comment_counter = 0
        truncated_comments = []
        for comment in comments.values():
            if comment_counter >= self.comment_options['comment_limit']:
                self.bot_log("Reached post's comment limit at: {}".format(comment_counter))
                break
            comment_counter += 1
            truncated_comments.append(comment)
        return truncated_comments

    def __call__(self):
        """
        Invokes RedditBot's primary function to do the following:
            * Get top content from subreddits' posts and comments
            * Write a speech with top content
            * Publish speech
        """
        self.bot_log('Initiating RedditBot to publish top content.')

        self.get_top_content()
        self.publish_speech()

        self.bot_log('Finished publishing top content.')

    def get_top_content(self):
        """
        Get top content from subreddits' posts and comments.
        """
        for subreddit in self.subreddits:
            self.get_subreddit_posts(subreddit)
            if self.subreddit_posts is None:
                raise Exception('Did not find any content for subreddit {}.'.format(subreddit))

            post_qualified_comments = self.get_post_qualified_comments()
            self.top_content_tree.update({subreddit: post_qualified_comments})

    def get_subreddit_posts(self, subreddit):
        """
        Get subreddit posts.

        :type subreddit: str
        """
        self.bot_log('Iterating subreddit: {}.'.format(subreddit))
        try:
            self.subreddit_posts = self.reddit_client.subreddit(subreddit).top(
                time_filter=self.post_options['time_filter'],
                limit=self.post_options['post_limit'])
        except Exception as message:
            self.bot_log('Error grabbing posts for subreddit: {}'.format(message))

        self.bot_log('Finished grabbing {} posts for subreddit: {}'.format(len([self.subreddit_posts]), subreddit))

    def publish_speech(self):
        """
        Publishes speech. Writes speech, converts text to audio, and uploads speech.
        """
        if len(self.top_content_tree) == 0:
            raise Exception('Did not find any content for subreddits {}.'.format(self.subreddits))
        self.store_speech()
        self.text_to_speech()
        self.upload_speech()

    def store_speech(self):
        """
        Writes speech for subreddits' top posts and comments.
        """
        self.update_subreddits()
        self.store_intro()
        self.store_body()
        self.store_outro()

    def store_intro(self):
        """
        Writes intro for the file about the subreddits.
        """
        self.bot_log('Storing intro.')

        content = "Here's what's happening with "
        content += self.get_human_readable_subreddit_list()
        content += "\nLet's get started."
        self.store(content)

        self.store(FileHelper.get_dictation_pause(1000), False)

    def store_body(self):
        """
        Writes body for the file for the top post and comments.
        """
        for subreddit, post_comments in self.top_content_tree.items():
            self.bot_log('Iterating subreddit: {}.'.format(subreddit))
            self.store_subreddit(subreddit)
            for post, comments in post_comments.items():
                self.store_post(post)
                for comment in comments:
                    self.store_comment(comment)
                self.store_segue()

    def store_subreddit(self, subreddit):
        """
        Writes segue to next post to file.

        :type subreddit: str
        """
        if len(self.subreddits) > 1:
            self.bot_log('Storing subreddit.')
            content = '\nIn r/{}...'.format(subreddit)
            self.store(content)
            self.store(FileHelper.get_dictation_pause(1000), False)

    def store_outro(self):
        """
        Writes intro for the file about the subreddits and comments.
        """
        self.bot_log('Storing outro.')

        content = '\nThat concludes our look at '
        content += self.get_human_readable_subreddit_list()
        content += '\nSmash that like button for less anxiety.'
        self.store(content)

    def store_segue(self):
        """
        Writes segue to next post to file.
        """
        self.bot_log('Storing segue.')
        self.store("\n Hmmm...kay\n")

    def store_post(self, post):
        """
        Writes subreddit post data to file.

        :type post: Submission
        """
        self.bot_log('Storing post.')

        self.store('\n***{}***\n {}\n\n'.format(post.title, post.selftext))
        self.store('[[{} - {}]]'.format(post.author, post.score), False)
        self.store(FileHelper.get_dictation_pause(1000), False)

    def store_comment(self, comment):
        """
        Writes comment data from subreddit post to file.

        :type comment: Comment
        """
        self.bot_log('Storing comment.')

        self.store('\n* {}\n'.format(comment.body))
        self.store('[[{} - {}]]'.format(comment.author, comment.score), False)
        self.store(FileHelper.get_dictation_pause(), False)

    def get_human_readable_subreddit_list(self):
        """
        Get grammatically correct list of subreddits for dictation.

        :rtype: str
        """
        self.bot_log('Getting human readable list of subreddits.')

        content = ''
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

    def update_subreddits(self):
        """
        Update any missing subreddits based on posts.
        """
        for post in self.subreddit_posts:
            if post.subreddit not in self.subreddits:
                self.subreddits.update({post.subreddit: None})

    def get_post(self, post_tag):
        """
        Gets subreddit post based on id or url.

        :type post_tag: str
        :rtype: Submission
        """
        query_tags = ['id', 'url']
        for query_tag in query_tags:
            kwargs = {query_tag: post_tag}
            try:
                post = self.reddit_client.submission(**kwargs)
            except:
                self.bot_log('Failed to find post by {}.'.format(query_tag))

        return post


RedditBot()()
