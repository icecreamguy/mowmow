$(document).ready(function() {
    // Pull as much as possible out of the DOM into variables
    var buttons = $(".button");
    var show_recent_photos_button = $("#show_recent_photos");
    var show_date_picker_button = $("#show_date_picker");
    var take_photo_button = $("#take_photo_button");
    var date_picker_container = $("#date_picker_container");
    var date_picker = $('#date_picker');
    var photo_display_header = $("#photo_display_header");
    var photo_display = $('#photo_display')

    // Create buttons
    buttons.button();

    // Hide the date picker
    date_picker_container.hide();

    // Bind events to the buttons
    show_recent_photos_button.click(update_recent_photos);

    show_date_picker_button.click(function(){
        date_picker_container.fadeToggle('fast');
    });

    date_picker.datepicker({
        onSelect: show_photos_by_date,
        dateFormat: 'yy-mm-dd'
    });

    take_photo_button.click(function() {
        // Activate the camera. if the camera class loads with a POST dictionary
        // key of "capture" it will take a photo. The value doesn't actually do
        // anything
        $.post('nomnom', { feed: 1 }, function(data){
            // After we get a (hopfully successful) response back, load/reload the
            // recent photos area.
            // TODO 
            // Add some error handling here
            result = $.parseJSON(data)
            if (result.result == 'locked'){
                $('#feedresult_text').html('Feeder locked! Bailey\'s either already\
                    been fed, or it isn\'t time to feed her yet.')
                    $('#feedresult_modal').modal('show')
            }
            else{
                $('#feedresult_text').html('Bailey fed! Check the photos to make\
                    sure she\'s still adorable. Which she is. Duh.')
                    $('#feedresult_modal').modal('show')
                update_recent_photos();
            }
        });
    });

    //Update the recent photos area on page load
    update_recent_photos();
});

function update_recent_photos(){
    $("#photo_display_header").html('Recent Photos');
    $("#photo_display").empty().hide();
    // Grab the 6 most recent photos. On success add them into the photo
    // display area
    recent_photos = $.getJSON('/photo/recent/8', function(recent_photos){
        parse_photos(recent_photos);
    });

    function setup(){
        $.getJSON('status', function(mow_status){
            next_nom_time = new Date(Date.parse(mow_status.next_nom_time));
            next_nom_start = new Date(Date.parse(mow_status.next_nom_start));
            last_nomtime = new Date(Date.parse(mow_status.last_nomtime));
            $('#next_nomtime').html(next_nom_time.toLocaleTimeString() + ' on ' +
                next_nom_time.toDateString());
            $('#next_nomtime_start').html(next_nom_start.toLocaleTimeString() + ' on ' +
                next_nom_start.toDateString());
            $('#last_nomtime').html(last_nomtime.toLocaleTimeString() + ' on ' +
                last_nomtime.toDateString());
        });
    }

    setup();
}

function show_photos_by_date(date){
    init_photo_display('Photos From ' + date);
    // Grab a list of the photos from the specified date. On success add them
    // into the photo display area
    photos_from_date = $.getJSON('photo/date/' + date, function(photos_from_date){
        parse_photos(photos_from_date);
    });
}

function init_photo_display(section_title){
    $("#photo_display_header").html(section_title);
    $("#photo_display").empty().hide();
}

function parse_photos(photo_array){
    // Iterate over the photos and add them to the photo display div
    $.each(photo_array, function(index,photo){
        $('<img>').attr({
            'src': photo.file_path + '/' + photo.file_name, 'class': 'photo'}).
                appendTo(photo_display);
        // Fade in the area so it looks cool
        $("#photo_display").fadeIn('slow');
    });
}

function print_r(objects){
    for (var object in objects){
        if (objects.hasOwnProperty(object)){
            alert(object + '\n' + objects[object]);
        }
    }
}
