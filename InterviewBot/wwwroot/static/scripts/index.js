$(document).ready(function() {
    /* Implement the logic required to zoom in on our family tree using buttons, rather than the OOTB scroll functionality. */
    var containerElement = document.querySelector("#family-tree-container");
    var currentZoomIndex = 5;
    var zoomValues = [0.5, 0.75, 0.85, 0.9, 0.95, 1];

    $("#zoom-in-button").on("click", function() {
        try {
            if(currentZoomIndex <= zoomValues.length - 1) {
                currentZoomIndex++;
                value = zoomValues[currentZoomIndex];
                containerElement.style["transform"] = `scale(${value})`
            }
        }
        catch(error) {
            console.error(error);
        }
    });

    $("#zoom-out-button").on("click", function() {
        if(currentZoomIndex > 0) {
            currentZoomIndex -= 1;
            value = zoomValues[currentZoomIndex];
            containerElement.style["transform"] = `scale(${value})`
        }
    });

    /* Implement some logic to display a help page to the user. */
    $("#help-button").on("click", function() {
        $("#help-window-container").dialog({
            height: 500,
            resizable: false,
            width: "35%"
        });
    });

    /* Logic to toggle the visibility of the introductory message, displayed when the page loads. */
    $("#rasa-chat-widget-container").on("click", function() {
        if ($("#intro-message-container").is(":visible")) {
            $("#intro-message-container").hide();
        }
    });
});