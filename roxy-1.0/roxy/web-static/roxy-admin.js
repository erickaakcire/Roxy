function updateUser()
{
	$.ajax({
		url: "/add_user.xml?username=" + $("input#userid").val() + "&password=" + $("input#secret").val(),
		success: function(data) 
		{
			$(data).find("status").each(function()
			{
				alert($(this).attr("message"));
			});
		}
	});
}

function deleteUser()
{
	$.ajax({
		url: "/delete_user.xml?username=" + $("input#userid").val(),
		success: function(data) 
		{
			$(data).find("status").each(function()
			{
				alert($(this).attr("message"));
			});
		}
	});
}

function fetchPassword()
{
	$.ajax({
		url: "/fetch_user.xml?username=" + $("input#userid").val(),
		success: function(data) 
		{
			$(data).find("status").each(function()
			{
				alert($(this).attr("message"));
			});
		}
	});
}
