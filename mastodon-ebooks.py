#!/usr/bin/python3
from mastodon import Mastodon
from bs4 import BeautifulSoup
from random import shuffle
import markovify
import html
import json
import os
import sys
import getopt

# init mastodon
mastodon = Mastodon(
  #replace values/files with your own
  client_id = 'clientcred.secret',
  access_token = 'usercred.secret',
  api_base_url = 'https://computerfairi.es'
)

# strip html tags for text alone
def strip_tags(content):
  soup = BeautifulSoup(html.unescape(content), 'html.parser')
  # remove mentions
  tags = soup.select('.mention')
  for i in tags:
    i.extract()
  # clear shortened link captions
  tags = soup.select('.invisible, .ellipsis')
  for i in tags:
    i.unwrap()
  # replace link text to avoid caption breaking
  tags = soup.select('a')
  for i in tags:
    i.replace_with(i.get_text())
  # strip html tags, chr(31) joins text in different html tags
  return soup.get_text('\n').strip()

# markovify subclass to use \0 as sentence separator
class MarkovModel(markovify.Text):
  def sentence_split(self, text):
    return text.split('\0')
  
# scrapes the accounts the bot is following to build corpus
def scrape():
  me = mastodon.account_verify_credentials()
  following = mastodon.account_following(me['id'])
  acctfile = 'accts.json'
  # acctfile contains info on last scraped toot id
  try:
    with open(acctfile, 'r') as f:
      acctjson = json.load(f)
  except:
    acctjson = {}
  
  print(acctjson)
  for acc in following:
    id = str(acc['id'])
    try:
      since_id = scrape_id(id, since=acctjson[id])
    except:
      since_id = scrape_id(id)
    acctjson[id] = since_id
  
  with open(acctfile, 'w') as f:
    json.dump(acctjson, f)
    
  # generate the whole corpus after scraping so we don't do at every runtime
  combined_model = None
  for (dirpath, _, filenames) in os.walk("corpus"):
    for filename in filenames:
      with open(os.path.join(dirpath, filename)) as f:
        model = MarkovModel(f, retain_original=False)
        if combined_model:
          combined_model = markovify.combine(models=[combined_model, model])
        else:
          combined_model = model
  with open('model.json','w') as f:
    f.write(combined_model.to_json())

def scrape_id(id, since=None):
  # excluding replies was a personal choice. i haven't made an easy setting for this yet
  toots = mastodon.account_statuses(id, since_id=since, exclude_replies=True)
  # if this fails, there are no new toots and we just return old pointer
  try:
    new_since_id = toots[0]['id']
  except:
    return since
  bufferfile = 'buffer.txt'
  corpusfile = 'corpus/%s.txt' % id
  i = 0
  with open(bufferfile, 'w') as output:
    while toots != None and len(toots) > 0:
      # writes current amount of scraped toots without breaking line
      i = i + len(toots)
      sys.stdout.write('\r%d' % i)
      sys.stdout.flush()
      filtered_toots = list(filter(lambda x: x['spoiler_text'] == "" and x['reblog'] is None and x['visibility'] in ["public", "unlisted"], toots))
      for toot in filtered_toots:
        output.write(strip_tags(toot['content'])+'\0')
      toots = mastodon.fetch_next(toots)
    # buffer is appended to the top of old corpus
    if os.path.exists(corpusfile):
      with open(corpusfile,'r') as old_corpus:
        output.write(old_corpus.read())
    directory = os.path.dirname(corpusfile)
    if not os.path.exists(directory):
      os.makedirs(directory)
    os.rename(bufferfile,corpusfile)
    sys.stdout.write('\n')
    sys.stdout.flush()
  return new_since_id

# returns a markov generated toot
def generate(length=None, seed_msg=''):
  modelfile = 'model.json'
  if not os.path.exists(modelfile):
    sys.exit('no model -- please scrape first')
  with open(modelfile, 'r') as f:
    reconstituted_model = markovify.Text.from_json(f.read())
  
  msg = ''
  if seed_msg is not '':
    list = seed_msg.split(' ')
    shuffle(list)
    for word in list:
      i = 500
      while i:
        test = generate_length(reconstituted_model, length)
        if word in test:
          msg = test
          break
        i = i - 1
      if msg is not '': break
    if not msg:
      msg = generate_length(reconstituted_model, length)
  else:
    msg = generate_length(reconstituted_model, length)
  return msg.replace(chr(31), "\n")
  
def generate_length(model, length=None):
  if length:
    return model.make_short_sentence(length)
  else:
    return model.make_sentence()

# perform a generated toot to mastodon
def toot():
  msg = generate(500)
  mastodon.toot(msg)
  print('Tooted: %s' % msg)

# simply prints a generated toot to the console
def console():
  print(generate())

# scan all notifications for mentions and reply to them
def reply():
  #get nofitications
  try:
    notifs = mastodon.notifications()
  except (KeyError):
    return
  #filter mentions
  mentions = list(filter(lambda x: x['type'] == 'mention', notifs))
  #iterate over them
  for status in mentions:
    acct = status['status']['account']['acct']
    id = status['status']['id']
    print (strip_tags(status['status']['content']))
    toot = (''.join(['@', acct, ' ', generate(400, strip_tags(status['status']['content']))]))[:500]
    print(toot)
    mastodon.status_post(toot, in_reply_to_id=id)
  #clear notifications
  mastodon._Mastodon__api_request('POST', '/api/v1/notifications/clear')

def usage():
  print('usage:')
  print('-t, --toot: generates and toots')
  print('-p, --print: generates and prints to console')
  print('-s, --scrape: scrapes following accounts')
  print('-r, --reply: replies to mentions')
  
def main(argv):
  try:                                
    opts, args = getopt.getopt(argv, "trps", ["toot", "reply", "print", "scrape"])
  except getopt.GetoptError:          
    usage()                         
    sys.exit(2)
  for opt, arg in opts:
    if opt in ('-t','--toot'):
      toot()
    elif opt in ('-r','--reply'):
      reply()
    elif opt in ('-p','--print'):
      console()
    elif opt in ('-s','--scrape'):
      scrape()

if __name__ == "__main__":
    main(sys.argv[1:])