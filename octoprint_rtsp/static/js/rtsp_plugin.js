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

        // This path will be: /plugin/rtsp/stream
        self.streamUrl = ko.pureComputed(function () {
            return window.location.protocol + "//" + window.location.host + "/plugin/rtsp/stream";
        });

        self.snapshotUrl = ko.pureComputed(function () {
            return window.location.protocol + "//" + window.location.host + "/plugin/rtsp/snapshot";
        });

        self.testPtz = function (direction) {
            $.ajax({
                url: API_BASEURL + "plugin/rtsp/control/" + direction,
                type: "POST",
                success: function (response) {
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
        // ViewModels: SettingsViewModel
        dependencies: ["settingsViewModel"],
        // Bind ONLY to our helper sections, NOT the whole settings div
        elements: ["#rtsp_plugin_settings_container"]
    });
});
