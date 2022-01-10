function emailCopyToClipBoard(userID) {
    var copiedText = document.getElementById('emailTooltipValue' + userID);
    navigator.clipboard.writeText(copiedText.innerText);
    var tooltipEl = document.getElementById('userEmailTooltip' + userID);
    // using jquery to change the tooltip title so that the admin knows that they have copied
    $(tooltipEl).attr('title', 'Copied to Clipboard!').tooltip('_fixTitle').tooltip('show')
}
function emailTooltipMouseOut(userID) {
    var tooltipEl = document.getElementById('userEmailTooltip' + userID);
    // using jquery to reset the tooltip title
    $(tooltipEl).attr('title', 'Copy to Clipboard').tooltip('_fixTitle').tooltip('show')
}
function usernameCopyToClipBoard(userID) {
    var copiedText = document.getElementById('usernameTooltipValue' + userID);
    navigator.clipboard.writeText(copiedText.innerText);
    var tooltipEl = document.getElementById('usernameTooltip' + userID);
    // using jquery to change the tooltip title so that the admin knows that they have copied
    $(tooltipEl).attr('title', 'Copied to Clipboard!').tooltip('_fixTitle').tooltip('show')
}
function usernameTooltipMouseOut(userID) {
    var tooltipEl = document.getElementById('usernameTooltip' + userID);
    // using jquery to reset the tooltip title
    $(tooltipEl).attr('title', 'Copy to Clipboard').tooltip('_fixTitle').tooltip('show')
}
function userIDCopyToClipBoard(userID) {
    var copiedText = document.getElementById('userIDTooltipValue' + userID);
    navigator.clipboard.writeText(copiedText.innerText);
    var tooltipEl = document.getElementById('userIDTooltip' + userID);
    // using jquery to change the tooltip title so that the admin knows that they have copied
    $(tooltipEl).attr('title', 'Copied to Clipboard!').tooltip('_fixTitle').tooltip('show')
}
function usernameTooltipMouseOut(userID) {
    var tooltipEl = document.getElementById('userIDTooltip' + userID);
    // using jquery to reset the tooltip title
    $(tooltipEl).attr('title', 'Copy to Clipboard').tooltip('_fixTitle').tooltip('show')
}