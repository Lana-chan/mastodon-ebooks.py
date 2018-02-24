# mastodon-ebooks.py

Simple ebooks-style bot for mastodon.py

Inspired by original work by Jess: https://github.com/Jess3Jane/mastodon-ebooks

## Improvements over other ebooks bots

* Scrapes only new toots, not entire list of statuses
* Separates corpus by account, making a multi-account ebooks easier to manage
* Does not require Heroku or Ruby
* "Smart" replies
* Cronjob friendly
* Ananas friendly

## Usage

1. Create a Mastodon account to be the ebooks bot
2. Follow the account(s) to be used as source material from bot
3. You can use a script [like this](https://gist.github.com/Lana-chan/b0d937968d22eca6dcd79a0524449f1d) to generate user secrets to be used by the ebooks script
4. Scrape the users by running: `./mastodon-ebooks.py -s`
5. Verify the markov works by running locally to console: `./mastodon-ebooks.py -p`
6. Toot a markovified status! `./mastodon-ebooks.py -t`

You can now set scraping and tooting to run periodically with cronjobs.

Optionally, you can also run `./mastodon-ebooks.py -r` regularly to check on notifications and reply to mentions.

### The Ananas Way

1. Create a Mastodon account to be the ebooks bot
2. Copy `config.cfg-sample` to `config.cfg`
   * Advanced users: You'll probably already have a config and secret keys for the bot. Just set it up as long as your config file can find the `ananaswrapper.ebooksBot` class.
3. Run `ananas --interactive config.cfg` and input the information for your bot account

That's it! The ananas wrapper is set to scrape daily, toot every 30 minutes and reply to mentions. You can find more info at the [ananas repo](https://github.com/chr-1x/ananas)
