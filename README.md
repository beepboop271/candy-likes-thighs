# candy-likes-thighs

Uhhhhhhhhhhhhhhhhhhhhhhhhh basically candy is really good at guessing Arknights characters just from thigh pictures...

So all this bot does is pick a small section of an arknights operator's image and you try to guess the character, increasing the radius of the section if needed.

edit: ok so its no longer just a discord bot, website is wip i guess who knows how that will turn out.

website progress:
- [x] joining, leaving games, working player list
- [x] chat
- [x] generate temporary images and send them to players
- [x] checking chat to see if someone guessed correctly to have scoring and a finished game
- [x] all above work without requiring all users to be connected to a single web server (but all web servers share one instance of redis)
- [x] implement cache for images (with smth like [nginx `proxy_cache_lock`](https://www.nginx.com/blog/benefits-of-microcaching-nginx/)) so that only 1 request for each image hits the web servers
- [ ] load balance and multiple instances of image+web servers running (pray 1 redis instance is enough)
- [ ] containers and kubernetes???<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>

- [ ] proper frontend
