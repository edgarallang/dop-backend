/* Author: Wilson Xu */

function hide_flask_message_container() {
    $('#flash_message_container').slideUp('fast');
}

$(document).ready(function() {
    

	$('#reset_password_form').on('submit', function(e){
		alert("HEY");
		e.preventDefault();
	});



    function isEmail(email) {
  		var regex = /^([a-zA-Z0-9_.+-])+\@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,4})+$/;
  		return regex.test(email);
	}

	function countChar(val) {
	    var len = val.value.length;
	    if (len >= 500) {
	      val.value = val.value.substring(0, 500);
	    } else {
	      $('#charNum').text(500 - len);
	    }
    };
})
