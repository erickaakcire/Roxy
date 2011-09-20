var direct = "DIRECT";

var proxy = "PROXY proxy.roxyproxy.org:58080; DIRECT";

function FindProxyForURL(url, host)
{
	if (url.length > 512)
		return direct;
		
	if (/\.css/.test(url))
		return direct;
	else if (/\.js/.test(url))
		return direct;
	else if (/\.png/.test(url))
		return direct;
	else if (/\.jpg/.test(url))
		return direct;
	else if (/\.JPG/.test(url))
		return direct;
	else if (/\.jpeg/.test(url))
		return direct;
	else if (/\.css/.test(url))
		return direct;
	else if (/\.ico/.test(url))
		return direct;
	else if (/\.gif/.test(url))
		return direct;
	else if (/\.mp3/.test(url))
		return direct;
	else if (/\.pls/.test(url))
		return direct;
	else if (/\.swf/.test(url))
		return direct;

	else if (/\.google\.com\/history\/feeds\/default\/subscriptions\/browser/.test(url))
		return direct;
	else if (/\.sun\.com/.test(url))
		return direct;
	else if (/\.oracle\.com/.test(url))
		return direct;
	else if (/edit\.client\.yahoo\.com/.test(url))
		return direct;
	else if (/outbrain\.com/.test(url))
		return direct;
	else if (/facebook\.com/.test(url))
		return direct;
	else if (/widgets\.digg\.com/.test(url))
		return direct;
	else if (/sharethis\.com/.test(url))
		return direct;
	else if (/doubleclick\.net/.test(url))
		return direct;
	else if (/fastclick\.net/.test(url))
		return direct;
	else if (/rememberthemilk\.com/.test(url))
		return direct;
	else if (/google\-analytics\.com/.test(url))
		return direct;
	else if (/sitemeter\.com/.test(url))
		return direct;
	else if (/quantserve\.com/.test(url))
		return direct;
	else if (/chartbeat\.net/.test(url))
		return direct;
	else if (/specificclick\.net/.test(url))
		return direct;
	else if (/googleapis\.com/.test(url))
		return direct;
	else if (/AdGardener\.com/.test(url))
		return direct;
	else if (/addthis\.com/.test(url))
		return direct;
	else if (/blogads\.com/.test(url))
		return direct;
	else if (/zedo\.com/.test(url))
		return direct;
	else if (/scorecardresearch\.com/.test(url))
		return direct;
	else if (/sphere\.com/.test(url))
		return direct;
	else if (/google\.com\/coop/.test(url))
		return direct;
	else if (/google\.com\/cse/.test(url))
		return direct;
	else if (/google\.com\/jsapi/.test(url))
		return direct;
	else if (/itunes\.apple\.com/.test(url))
		return direct;
	else if (/tunes\.apple\.com/.test(url))
		return direct;
	else if (/phobos\.apple\.com/.test(url))
		return direct;
	else if (/kts\-af\.net/.test(url))
		return direct;
	else if (/edgesuite\.net/.test(url))
		return direct;
	else if (/thawte\.com/.test(url))
		return direct;

	else if (/webmail/.test(host))
		return direct;

	else if (/c\.youtube\.com/.test(url))
		return direct;

	else if (/captcha/.test(url))
		return direct;

	else if (/wordpress\.com\/remote\-login/.test(url))
		return direct;
	else if (/wp\-admin/.test(url))
		return direct;
	else if (/wp\-content\/themes/.test(url))
		return direct;
	else if (/wp\-content\/plugins/.test(url))
		return direct;

	else if (/noir\.bloomberg\.com/.test(url))
		return direct;

	else if (/\.mac\.com/.test(url))
		return direct;
	else if (/800notes\.com/.test(url))
		return direct;
	else if (/googlesyndication\.com/.test(url))
		return direct;
	else if (/safebrowsing\.clients\.google\.com/.test(url))
		return direct;
	else if (/www\.jaynick\.com\/RTP\/ComEdRTPxml\.php/.test(url))
		return direct;
	else if (/comodoca\.com/.test(url))
		return direct;
	else if (/crl\.comodo\.net/.test(url))
		return direct;
	else if (/2o7\.net/.test(url))
		return direct;
	else if (/jpusa\.net/.test(url))
		return direct;
	else if (/fbcdn\.net/.test(url))
		return direct;
	else if (/platform0\.twitter\.com/.test(url))
		return direct;

	else if (/amazon\.com/.test(url))
		return direct;
	else if (/ebay\.com/.test(url))
		return direct;
	else if (/craigslist\.org/.test(url))
		return direct;
	else if (/slickdeals\.net/.test(url))
		return direct;
	else if (/newegg\.com/.test(url))
		return direct;
	else if (/staples\.com/.test(url))
		return direct;
	else if (/shopping\.google\.com/.test(url))
		return direct;
	
	else if (url.indexOf(host + ":") != -1)
		return direct;

	else if (/google\.com\/complete/.test(url))
		return direct;
	else if (/\.atdmt\.com/.test(url))
		return direct;
	else if (/\.admeld\.com/.test(url))
		return direct;
	else if (/api\.twitter\.com/.test(url))
		return direct;
	else if (/adnxs\.com/.test(url))
		return direct;
	else if (/collective\-media\.net/.test(url))
		return direct;
	else if (/verisign\.com/.test(url))
		return direct;
	else if (/tynt\.com/.test(url))
		return direct;
	else if (/platform2\.twitter\.com/.test(url))
		return direct;
	else if (/platform1\.twitter\.com/.test(url))
		return direct;
	else if (/safebrowsing\-cache\.google\.com/.test(url))
		return direct;
	else if (/mediaplex\.com/.test(url))
		return direct;
	else if (/interclick\.com/.test(url))
		return direct;
	else if (/adbrite\.com/.test(url))
		return direct;
	else if (/adsonar\.com/.test(url))
		return direct;
	else if (/adgardener\.com/.test(url))
		return direct;
	else if (/doubleverify\.com/.test(url))
		return direct;
	else if (/atwola\.com/.test(url))
		return direct;
	else if (/advertising\.com/.test(url))
		return direct;
	else if (/statcounter\.com/.test(url))
		return direct;
	else if (/bizographics\.com/.test(url))
		return direct;
	else if (/adsfaq\.us/.test(url))
		return direct;
	else if (/halogennetwork\.com/.test(url))
		return direct;
	else if (/a\.digg\.com/.test(url))
		return direct;
	else if (/google\.com\/buzz\/api/.test(url))
		return direct;
	else if (/yieldmanager\.com/.test(url))
		return direct;
	else if (/invitemedia\.com/.test(url))
		return direct;
	else if (/postup\.com/.test(url))
		return direct;
	else if (/conduit\-services\.com/.test(url))
		return direct;
	else if (/kissmetrics\.com/.test(url))
		return direct;
	else if (/godaddy\.com/.test(url))
		return direct;
	else if (/qualtrics\.com/.test(url))
		return direct;
	else if (/netflix\.com/.test(url))
		return direct;
	else if (/www\.wow\.com/.test(url))
		return direct;
	else if (/widgets/.test(url))
		return direct;
	else if (/\.admonkey\./.test(url))
		return direct;
	else if (/\.secureserver\./.test(url))
		return direct;
	else if (/embargo\.theabisgroup\.com/.test(url))
		return direct;

	else if (/ytimg\.com/.test(url))
		return direct;
	else if (/scene7\.com/.test(url))
		return direct;
	else if (/coremetrics\.com/.test(url))
		return direct;
	else if (/gravatar\.com/.test(url))
		return direct;

	else if (/horchow\.com/.test(url))
		return direct;
	else if (/neimanmarcus\.com/.test(url))
		return direct;

	else if (/diigo\.com/.test(url))
		return direct;
	else if (/toolbar\.google\.com/.test(url))
		return direct;
	else if (/zynga\.com/.test(url))
		return direct;
	else if (/\/json\//.test(url))
		return direct;
	else if (/\.fm\.net/.test(url))
		return direct;
	else if (/\.flickr\.com/.test(url))
		return direct;
	else if (/\.yimg\.com/.test(url))
		return direct;
	else if (/\.mm\.bing\.net/.test(url))
		return direct;
	else if (/gmail\.com/.test(url))
		return direct;
	else if (/gallery\.me\.com/.test(url))
		return direct;
	else if (/\.adserver\.yahoo\.com/.test(url))
		return direct;
	else if (/zone\.msn\.com\/windows\/ad\.asp/.test(url))
		return direct;
	else if (/zone\.msn\.com\/windows\/en\/ad/.test(url))
		return direct;
	else if (/virtualearth\.net/.test(url))
		return direct;
	else if (/ebayimg\.com/.test(url))
		return direct;
	else if (/mathtag\.com/.test(url))
		return direct;
	else if (/googleadservices\.com/.test(url))
		return direct;
	else if (/chicagopoints\.chicagotribune\.com/.test(url))
		return direct;

	else if (/pandora\.com/.test(url))
		return direct;

	else if (/llnwd\.net/.test(url))
		return direct;
	else if (/\/cdn\./.test(url))
		return direct;
	else if (/addelivery\.thestreet\.com/.test(url))
		return direct;
	else if (/ad\.fed\.adecn\.com/.test(url))
		return direct;
	else if (/mibbit\.com/.test(url))
		return direct;
	else if (/blizzard\.com/.test(url))
		return direct;
	else if (/80\.157\.169\.38/.test(url))
		return direct;
	else if (/\.chase\.com/.test(url))
		return direct;

	else if (/\/mail\./.test(url))
		return direct;
	else if (/\.mail\./.test(url))
		return direct;

	else if (/ocsp\./.test(url))
		return direct;

	else if (/\/ad\//.test(url))
		return direct;
	else if (/\/ads\//.test(url))
		return direct;
	else if (/\/ads\./.test(url))
		return direct;
		
	else if (/^https/.test(url))
		return direct;

	else if (/^http/.test(url))
		return proxy;
		
	return direct;
}
