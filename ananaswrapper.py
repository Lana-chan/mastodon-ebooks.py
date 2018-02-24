from ananas import PineappleBot, hourly, schedule, reply, daily
ebooks = __import__("mastodon-ebooks")

class ebooksBot(PineappleBot):
  def start(self):
    try:
      self.visibility = str(self.config.visibility)
      if self.visibility not in ['public', 'unlisted', 'private', 'direct']:
        self.visibility = 'unlisted'
    except:
      self.visibility = 'unlisted'
    try:
      self.bot_name = str(self.config.bot_name)
    except:
      self.bot_name = ""
    self.scrape()
  
  @daily()
  def scrape(self):
    ebooks.scrape(self.mastodon)
    
  @hourly(minute=0)
  @hourly(minute=30)
  def toot(self):
    msg = ebooks.generate(500)
    self.mastodon.status_post(msg, visibility = self.visibility)
    
  @reply
  def reply(self, mention, user):
    msg = ebooks.strip_tags(mention['content'])
    tgt = user['acct']
    irt = mention['id']
    vis = mention['visibility']
    rsp = "@{} {}".format(tgt, ebooks.generate(400, msg))[:500]
    self.mastodon.status_post(rsp, in_reply_to_id = irt, visibility = vis)