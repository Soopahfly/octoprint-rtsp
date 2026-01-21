/*
 * View model for OctoPrint-RTSP
 *
 * Author: Nathen Fredrick
 * License: AGPLv3
 */
$(function () {
    function RtspViewModel(parameters) {
        var self = this;

        self.settingsViewModel = parameters[0];

        // Generate URLs
        var baseUrl = window.location.protocol + "//" + window.location.host;

        // Create our own observables
        self.streamUrl = ko.observable(baseUrl + "/plugin/rtsp/stream");
        self.snapshotUrl = ko.observable(baseUrl + "/plugin/rtsp/snapshot");
        self.previewUrl = ko.observable(baseUrl + "/plugin/rtsp/snapshot?t=" + Date.now());

        self.refreshPreview = function() {
            self.previewUrl(baseUrl + "/plugin/rtsp/snapshot?t=" + Date.now());
        };

        self.testPtz = function (direction) {
            $.ajax({
                url: API_BASEURL + "plugin/rtsp/control/" + direction,
                type: "POST",
                success: function () {
                    new PNotify({
                        title: "PTZ Success",
                        text: "Command " + direction + " sent successfully.",
                        type: "success"
                    });
                },
                error: function (xhr) {
                    new PNotify({
                        title: "PTZ Error",
                        text: xhr.responseText || "Unknown error",
                        type: "error"
                    });
                }
            });
        };

        // Refresh preview when settings opened
        self.onSettingsShown = function() {
            self.refreshPreview();
        };
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: RtspViewModel,
        dependencies: ["settingsViewModel"],
        elements: ["#settings_plugin_rtsp"]
    });
});
