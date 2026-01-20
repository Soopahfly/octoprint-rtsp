/*
 * View model for OctoPrint-RTSP
 *
 * Author: Antigravity
 * License: AGPLv3
 */
$(function () {
    function RtspViewModel(parameters) {
        var self = this;

        self.settingsViewModel = parameters[0];

        // Generate URLs
        var baseUrl = window.location.protocol + "//" + window.location.host;
        self.streamUrl = ko.observable(baseUrl + "/plugin/rtsp/stream");
        self.snapshotUrl = ko.observable(baseUrl + "/plugin/rtsp/snapshot");

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
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: RtspViewModel,
        dependencies: ["settingsViewModel"],
        elements: ["#rtsp_plugin_settings_container"]
    });
});
