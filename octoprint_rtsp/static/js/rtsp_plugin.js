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

        // Preview URL with cache buster for refresh functionality
        self.previewUrl = ko.observable(baseUrl + "/plugin/rtsp/snapshot?t=" + Date.now());

        self.refreshPreview = function() {
            // Update preview URL with new timestamp to bust cache
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

        // Called when settings dialog is shown - manually apply bindings
        self.onSettingsShown = function() {
            var container = document.getElementById("rtsp_plugin_settings_container");
            if (container && !container._boundByRtsp) {
                container._boundByRtsp = true;
                // Create a combined viewmodel for the template
                var combinedVm = {
                    settings: self.settingsViewModel.settings.plugins.rtsp,
                    streamUrl: self.streamUrl,
                    snapshotUrl: self.snapshotUrl,
                    previewUrl: self.previewUrl,
                    refreshPreview: self.refreshPreview,
                    testPtz: self.testPtz
                };
                ko.applyBindings(combinedVm, container);
            }
        };
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: RtspViewModel,
        dependencies: ["settingsViewModel"],
        elements: ["#rtsp_plugin_settings_container"]
    });
});
