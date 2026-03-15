// =============================================================
// GOOGLE APPS SCRIPT — Email Subscription for AI Career Transition
// =============================================================
//
// HOW TO DEPLOY (2 minutes):
//
// 1. Go to https://script.google.com and log in with your Gmail
// 2. Click "+ New project"
// 3. Delete any code in the editor and paste THIS ENTIRE FILE
// 4. Click the floppy disk icon (Save), name the project "AI Career Transition Subscribers"
// 5. Click "Deploy" (top right) → "New deployment"
// 6. Click the gear icon next to "Select type" → choose "Web app"
// 7. Set "Execute as" → "Me"
// 8. Set "Who has access" → "Anyone"
// 9. Click "Deploy"
// 10. It will ask for permissions — click "Authorize access" → choose your Google account → "Allow"
// 11. Copy the "Web app URL" it gives you (starts with https://script.google.com/macros/...)
// 12. Paste that URL into blog.html where it says PASTE_YOUR_GOOGLE_SCRIPT_URL_HERE
//
// That's it! Emails will appear in a Google Sheet called "AI Career Transition Subscribers"
// in your Google Drive.
// =============================================================

var SHEET_NAME = 'Subscribers';
var SPREADSHEET_NAME = 'AI Career Transition - Email Subscribers';

function getOrCreateSpreadsheet() {
  var files = DriveApp.getFilesByName(SPREADSHEET_NAME);

  if (files.hasNext()) {
    return SpreadsheetApp.open(files.next());
  }

  var ss = SpreadsheetApp.create(SPREADSHEET_NAME);
  var sheet = ss.getActiveSheet();
  sheet.setName(SHEET_NAME);
  sheet.appendRow(['Email', 'Date Subscribed', 'Source Page']);
  sheet.getRange('1:1').setFontWeight('bold');
  sheet.setColumnWidth(1, 300);
  sheet.setColumnWidth(2, 200);
  sheet.setColumnWidth(3, 200);
  return ss;
}

function processSubscription(email, source) {
  if (!email || email.indexOf('@') === -1 || email.indexOf('.') === -1) {
    return sendResponse('error', 'Please enter a valid email address.');
  }

  var ss = getOrCreateSpreadsheet();
  var sheet = ss.getSheetByName(SHEET_NAME);

  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.appendRow(['Email', 'Date Subscribed', 'Source Page']);
    sheet.getRange('1:1').setFontWeight('bold');
  }

  var existingData = sheet.getDataRange().getValues();
  for (var i = 1; i < existingData.length; i++) {
    if (existingData[i][0].toString().toLowerCase() === email) {
      return sendResponse('duplicate', 'You are already subscribed!');
    }
  }

  var now = new Date();
  var dateStr = Utilities.formatDate(now, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss');
  sheet.appendRow([email, dateStr, source]);

  return sendResponse('success', 'Thanks for subscribing!');
}

function doGet(e) {
  try {
    var email = (e.parameter.email || '').trim().toLowerCase();
    var source = e.parameter.source || 'blog.html';

    if (!email) {
      return sendResponse('ok', 'Subscription endpoint is working.');
    }

    return processSubscription(email, source);
  } catch (err) {
    return sendResponse('error', 'Something went wrong. Please try again.');
  }
}

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var email = (data.email || '').trim().toLowerCase();
    var source = data.source || 'blog.html';
    return processSubscription(email, source);
  } catch (err) {
    return sendResponse('error', 'Something went wrong. Please try again.');
  }
}

function sendResponse(status, message) {
  return ContentService
    .createTextOutput(JSON.stringify({ status: status, message: message }))
    .setMimeType(ContentService.MimeType.JSON);
}
