/* Author: Wilson Xu */

function hide_flask_message_container() {
    $('#flash_message_container').slideUp('fast');
}

$(document).ready(function() {
    

	$('#reset_password_form').on('submit', function(e){
		e.preventDefault();
		var count = $("#password_input").val().length;
		if(count >= 6){
			e.submit();
		}else{
			$("#error_message").fadeIn();
		}
	});
})
