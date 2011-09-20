$.ajaxSetup ({ cache: false });

function loadFullUserHistory(page)
{
	$("td#full-history").load("/full_history.xml?p=" + page , function(response, status, xhr) 
	{
		if (status == "error") 
		{
			var msg = "Sorry but there was an error: ";
			$('td#recent-sites').html(msg + xhr.status + " " + xhr.statusText);
		}
		else
		{
			$("td#full-history").append("");
		}
		
		$("a.delete-domain").corner("5px");
		$("a.blacklist-domain").corner("5px");
		
		$("div.section-header").corner("5px");
		
		$("div#content").corner("15px");
	});

	$("div#user-blacklist").load("/user-blacklist.xml", function(response, status, xhr) 
	{
		$("a.private_button").corner("5px");

		$("div#content").corner("15px");
	});
}

function deleteDomain(domain, session)
{
	if (confirm("Are you sure you want to delete this ONE instance of '" + domain + "' from the logs?"))
	{
		$.ajax({
				url: "/delete_domain.json?domain=" + domain + "&session=" + session,
				dataType: 'json',
				data: { "foo": "bar" },
				success: function(data, ts, xhr) 
				{
					alert(data.message);
				
					loadFullUserHistory(0);
				}
		});
	}
}

function blacklistDomain(domain, silent)
{
	if (confirm("Are you sure you want to blacklist '" + domain + "'? This action will remove ALL logged entries from the dataset, and Roxy will not log the domain in the future."))
	{
		$.ajax({
				url: "/blacklist_domain.json?domain=" + domain,
				dataType: 'json',
				data: { "foo": "bar" },
				success: function(data, ts, xhr) 
				{
					if (!silent)
					{
						alert(data.message);
					}
					
					loadFullUserHistory(0);
				}
		});
	}
}

function loadUserHistory()
{
	$("td#recent-sites").load("/history.xml", function(response, status, xhr) 
	{
		if (status == "error") 
		{
			var msg = "Sorry but there was an error: ";
			$('td#recent-sites').html(msg + xhr.status + " " + xhr.statusText);
		}
		else
		{
			$("td#recent-sites").append("");
		}
		
		$("a.delete-domain").corner("5px");
		$("a.blacklist-domain").corner("5px");
		
		$("div.section-header").corner("5px");

		$("div#content").corner("15px");
	});
}

function myBlacklist()
{
	$("div#my-blacklist").load("/my-blacklist.xml", function(response, status, xhr) 
	{

	});
}

function removeBlacklist(domain)
{
	$.ajax({
			url: "/remove-blacklist.xml?domain=" + domain,
			dataType: 'xml',
			data: { "foo": "bar" },
			success: function(data, ts, xhr) 
			{
				alert("'" + domain + "' removed from blacklist.");
				
				myBlacklist();
			}
	});
}

function setCookie(name,value)
{
	var expiredays = 365;
	
	var exdate = new Date();
	exdate.setDate(exdate.getDate() + expiredays);

	document.cookie = name + "=" + escape(value) + ";expires=" + exdate.toUTCString();
}

function getCookie(name)
{
	if (document.cookie.length > 0)
	{
		var start = document.cookie.indexOf(name + "=");
		
		if (start != -1)
		{
			start = start + name.length + 1;
			var end = document.cookie.indexOf(";", start);

			if (end == -1)
			{
				end = document.cookie.length;
			}
			
			return unescape(document.cookie.substring(start, end));
		}
	}

	return "";
}


/* function setCookie (name, value)
{
	var today = new Date();
	today.setTime(today.getTime());

	var expires = 365 * 1000 * 60 * 60 * 24;

	var expires_date = new Date(today.getTime() + (expires));

	document.cookie = name + "=" +escape(value) +
		((expires) ? ";expires=" + expires_date.toGMTString() : "") +
		";path=/;domain=;";
}

function getCookie(name)
{
	var a_all_cookies = document.cookie.split(';');
	var a_temp_cookie = '';
	var cookie_name = '';
	var cookie_value = '';
	var b_cookie_found = false; // set boolean t/f default f

	for (i = 0; i < a_all_cookies.length; i++)
	{
		a_temp_cookie = a_all_cookies[i].split('=');
		cookie_name = a_temp_cookie[0].replace(/^\s+|\s+$/g, '');

		if (cookie_name == name)
		{
			b_cookie_found = true;
			if (a_temp_cookie.length > 1)
				cookie_value = unescape(a_temp_cookie[1].replace(/^\s+|\s+$/g, ''));

			return cookie_value;
		}

		a_temp_cookie = null;
		cookie_name = '';
	}

	if (!b_cookie_found)
		return null;
} */

function loadUserStatus(redirect)
{
	$("td#user-status").html("");
	
	$("td#user-status").load("/status.xml", function(response, status, xhr) 
	{
		$("div.section-header").corner("5px");

		if (status == "error") 
		{
			var msg = "Sorry but there was an error: ";
			$('td#user-status').html(msg + xhr.status + " " + xhr.statusText);
		}
		else
		{
			$("td#user-status").append("");
		}
		
		$("div.subheader").corner("5px");
		$("a.regular_button").corner("5px");
		$("a.private_button").corner("5px");
		$("a.guest_button").corner("5px");

		var userid = getCookie("username"); // $.cookie("username");
		var password = getCookie("password"); // $.cookie("password");

		if (userid !== null)
		{
			$('input#userid').val(userid);
		}
		
		if (password !== null)
		{
			$('input#password').val(password);
		}
		
		if (response.indexOf("Active:") > 0)
		{
			var new_location = unescape(location.href.replace("http://proxy.roxyproxy.org/?referrer=", ""));

			if (new_location.indexOf("http://proxy.roxyproxy.org/") == -1)
			{
				window.location = new_location;
			}
		}

		if ($("td#recent-sites"))
		{
			loadUserHistory();
		}

		$("div#content").corner("15px");
	});
}

function loadUsersSessions()
{
	$("div#user-session-history").load("/all_user_sessions.xml", function(response, status, xhr)
	{
		$("div#user-session-history").attr("style", "width:530px");

		$("div#content").corner("15px");
	});
}


$(document).ready(function()
{
	$("a.update_button").corner("5px");
	$("a.delete_button").corner("5px");
	$("a.search_button").corner("5px");

	$('div#service-updates').load('/service.xml');	

	$("div#sidebar").load("/sidebar.xml", function(response, status, xhr)
	{
		$("div#content").corner("15px");
		$("div#title").corner();
		$("div.section-header").corner("5px");
		
		$("a.regular_button").corner("5px");
		$("a.private_button").corner("5px");
		$("a.guest_button").corner("5px");
	});

	$("div#meta-sidebar").load("/meta-sidebar.xml", function(response, status, xhr)
	{
		$("div#content").corner("15px");
		$("div#title").corner();
		$("div.section-header").corner("5px");
		
		$("a.regular_button").corner("5px");
		$("a.private_button").corner("5px");
		$("a.guest_button").corner("5px");
	});

	if ($(this).find("div#my-blacklist"))
	{
		myBlacklist();
	}

	if ($(this).find("td#user-status"))
	{
		loadUserStatus(false);
	}
	
	if ($(this).find("td#full-history"))
	{
		loadFullUserHistory(0);
	}
	
	if ($(this).find("div#user-session-history"))
	{
		loadUsersSessions();
	}

	$("div.section-header").corner("5px");
});

function expireSession()
{
	$.get("/expire_session", {}, function (data)
	{
		loadUserStatus(false);
	});
}

function createSession()
{
	var userid = $('input#userid').val();
	var password = $('input#password').val();

//	$.cookie("username", userid);
//	$.cookie("password", password);

	setCookie("username", userid);
	setCookie("password", password);
	
	if (userid !== "")
	{
		$.get("/create_session?userid=" + userid + "&password=" + password, {}, function (data)
		{
			var redirect = false;
			
			$(data).find("status").each(function()
			{
				if ($(this).attr("go") === "true")
				{
					redirect = true;
				}
				else			
				{
					alert($(this).attr("message"));
				}
			});

			loadUserStatus(redirect);
		});
	}
	else
	{
		alert("Please enter a valid User ID.");
	}
}

function privateSession()
{
	var userid = $('input#userid').val();
	var password = $('input#password').val();

//	$.cookie("username", userid);
//	$.cookie("password", password);

	setCookie("username", userid);
	setCookie("password", password);

	$.get("/private_session?userid=" + userid + "&password=" + password, {}, function (data)
	{
		var redirect = false;
			
		$(data).find("status").each(function()
		{
			if ($(this).attr("go") === "true")
			{
				redirect = true;
			}
			else			
			{
				alert($(this).attr("message"));
			}
		});

		loadUserStatus(redirect);
	});
}

function guestSession()
{
	var userid = $('input#userid').val();
	var password = $('input#password').val();

//	$.cookie("username", userid);
//	$.cookie("password", password);

	$.get("/private_session?userid=guest&password=", {}, function (data)
	{
		var redirect = false;
			
		$(data).find("status").each(function()
		{
			if ($(this).attr("go") === "true")
			{
				redirect = true;
			}
			else			
			{
				alert($(this).attr("message"));
			}
		});

		loadUserStatus(redirect);
	});
}

function blacklist()
{
	var domain = $('input#blacklist_domain').val();

	blacklistDomain(domain, true);
	
	loadFullUserHistory(0);
}

