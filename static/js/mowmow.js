var current_photos = "";
var stats_template = $('#stats_template').html();
var new_account_submitted = false;

$(document).ready(function() {
    // Pull as much as possible out of the DOM into variables
    var buttons = $(".button");
    var show_recent_photos_button = $("#show_recent_photos");
    var take_photo_button = $("#take_photo_button");
    var date_picker_container = $("#date_picker_container");
    var date_picker = $('#date_picker');
    var photo_display_header = $("#photo_display_header");
    var thumbs = $('#thumbs');
    var loading_img = $('#loading_img');
    var thumbnails_list = $('#thumbs');
    var hidden_elements = $('.hidden');
    var auth_token = $.cookies.get('auth_token');
    var logout_button = $('#logout');
    
    hidden_elements.hide();

    // Create buttons
    buttons.button();

    // Hide the date picker
    date_picker_container.hide();

    // Bind events to the buttons
    show_recent_photos_button.click(update_recent_photos);

    date_picker.datepicker({
        onSelect: show_photos_by_date,
        dateFormat: 'yy-mm-dd'
    });

    $(document).on("click", "#take_photo_button", function() {
        // Activate the camera. if the camera class loads with a POST dictionary
        // key of "capture" it will take a photo. The value doesn't actually do
        // anything
        loading_img.show();
        $.post('api/nomnom', { feed: 1 }, function(data){
            // After we get a (hopfully successful) response back, load/reload the
            // recent photos area.
            // TODO 
            // Add some error handling here
            var result = $.parseJSON(data);
            if (result.result == 'locked'){
                $('#feedresult_text').html('Feeder locked! Bailey\'s either already\
                    been fed, or it isn\'t time to feed her yet.');
                $('#feedresult_modal').modal('show');
            }
            else if (result.result == 'unauthorized') {
                $('#feedresult_text').html('Please log in or create an account \
                    first');
                $('#feedresult_modal').modal('show');
            }
            else{
                $('#feedresult_text').html('Bailey fed! Check the photos to make\
                    sure she\'s still adorable. Which she is. Duh.');
                $('#feedresult_modal').modal('show');
                update_recent_photos();
            }
            loading_img.hide();
        });
    });

    logout_button.click(function(){
        logout_user(auth_token);
    });
        
    //bind events to forms
    $('#login_form').submit(function () {
        $('#loading_image_2').show();
        $.post('api/login/existing', $(this).serialize(), function (token) {
            if (token != 'false') {
                $.cookies.set('auth_token', token);
                $('#user_confirm').html('Logged in!').show().fadeOut(2000);
                $('#user_err').hide();
                setup();
            }
            else {
                $('#user_err').html('Incorrect email or password').show()
                    .fadeOut(2000);
                setup();
            }
        });
        return false;
    });

    $('#new_account_form').submit(function () {
            if (new_account_submitted){
                return false;
            }
            new_account_submitted = true
        $('#loading_image_3').show();
        $.post('api/login/new', $(this).serialize(), function (data) {
            if (data.problems){
                $('#user_confirm').hide();
                var alert_template = $('#new_account_alert_template').html();
                $('#new_account_alert_text').html('')
                $('#new_account_alert_text').append(Mustache.to_html(alert_template,
                        data));
                $('#new_account_alert').show();
                // Scroll up to the error list
                $('html, body').animate({
                    scrollTop: $('#new_account_alert_text').offset().top - 100
                }, 200);
                $('#loading_image_3').hide();
                new_account_submitted = false;
            }
            else{
                $('#new_account_alert').alert('close');
                $('#new-account-expander').collapse();
                $('#user_confirm').html(data.message).fadeIn();
                $('#new-account-confirm-modal').modal();
                $('html, body').animate({
                    scrollTop: $('body').offset().top - 60
                }, 200);
                $.cookies.set('auth_token', data.token);
                $('#loading_image_3').hide();
                new_account_submitted = false;
                setup();
            }
        }, "json");
        return false;
    });

    // Attach click event handler on all future individual photos to show
    // a modal with that photo
    thumbnails_list.on("click", "li div", function (event) {
        src = $(this).children('img').attr('src');
        index = $(this).children('img').attr('data-photo_id');
        label = $(this).children('span').html();
        show_photo(current_photos[index])
    });

    //Update the recent photos area on page load
    update_recent_photos();
    
    if (auth_token) {
        auth_user(auth_token);
    }
});

function logout_user(auth_token) {
    $.post('api/logout', {auth_token:auth_token}, function(data) {
        if (data) {
            $('#user_confirm').html('Logged out successfully').show().fadeOut(2000);
        }
        else {
            $('#user_confirm').html('There was a problem logging you out').show()
                .fadeOut(2000);
        }

    });
    $.cookies.del('auth_token');
    setup();
}

function update_recent_photos(){
    $("#photo_display_header").html('Recent Photos');
    $("#thumbs").empty().hide();
    // Grab the 8 most recent photos. On success add them into the photo
    // display area
    $.getJSON('api/photo/recent/8', function(recent_photos){
        current_photos = recent_photos;
        parse_photos();
    });

    setup();
}

function setup(){
    $.getJSON('api/status', function(mow_status){
        var status_template = $('#status_template').html();

        //if (mow_status.lock){ mow_status.lock = 'No'; }
        //else{ mow_status.lock = 'Yes'; }

        mow_status.last_nomtime = new Date(Date.parse(mow_status.last_nomtime));
        mow_status.last_nomtime = mow_status.last_nomtime.toLocaleTimeString() +
            ' ' + mow_status.last_nomtime.toLocaleDateString();
    
        // Customize the status a little if the user was the last person to
        // feed Bailey
        if (mow_status.last_feeder == mow_status.user_name) {
            mow_status.baileys_hero = true;
            mow_status.last_feeder = 'you';
        }
        
        $('#status_area').html(Mustache.to_html(status_template, mow_status));
        if (mow_status.user_name) {
            $('#user_name').html(mow_status.user_name);
            $('.logged_out').hide();
            $('.logged_in').show();
        }
        else {
            $('#login_form').show();
            $('.logged_in').hide();
            $('.logged_out').show();
        } 

        // fill placeholders in IE with this sweet plugin from
        // https://github.com/jamesallardice/Placeholders.js
        Placeholders.init();

        // Hide the loading image in case anything was loading
        $("#loading_image_2").hide();
        $("#loading_image_3").hide();
    });
    $.getJSON('api/stats/top_users', function (top_users) {
        $('#stats_area').html(Mustache.to_html(stats_template, top_users));
    });
}


function show_photos_by_date(date){
    init_photo_display('Photos From ' + date);
    // Grab a list of the photos from the specified date. On success add them
    // into the photo display area
    $.getJSON('api/photo/date/' + date, function(photos_from_date){
        current_photos = photos_from_date
        parse_photos();
    });
}

function init_photo_display(section_title){
    $("#photo_display_header").html(section_title);
    $("#thumbs").empty().hide();
}

function parse_photos(){
    // Iterate over the photos and add them to the photo display div
    var photo_template = $('#photo_template').html();
    $.each(current_photos, function(index,photo){
        photo.index = index;
        photo.thumb_file_name = photo.file_name.replace('.png','_thumb.png');
        if (!photo.cycle_name){
            photo.cycle_name = 'unknown';
        }
        $('#thumbs').append(Mustache.to_html(photo_template, photo));
        // Fade in the area so it looks cool
        $("#thumbs").fadeIn('slow');
    });

    // Fix for margin bug in Bootstrap thumbnail, by users 'brunolazzaro' and 'toze'
    // on the bootstrap bug tracker
    (function($){
        $('.row-fluid ul.thumbnails li.span6:nth-child(2n + 3)')
            .css('margin-left','0px');
        $('.row-fluid ul.thumbnails li.span4:nth-child(3n + 4)')
            .css('margin-left','0px');
        $('.row-fluid ul.thumbnails li.span3:nth-child(4n + 5)')
            .css('margin-left','0px'); 
    })(jQuery);
}

function print_r(objects){
    var string = ''
    for (var object in objects){
        if (objects.hasOwnProperty(object)){
            string += object + '\n' + objects[object];
        }
    }
    return string;
}

function show_photo (photo) {
    var photo_modal = $('#photo_modal');
    var modal_label = $('#photo_label');
    var modal_image = $('#modal_image');
    modal_label.html(photo.time_stamp + ', ' + photo.cycle_name + ' cycle');
    modal_image.attr('src', (photo.file_path + '/' + photo.file_name));
    photo_modal.modal('show');
}

function auth_user (auth_token) {
    $.getJSON('api/login/auth/' + auth_token, function () {
    });
}
