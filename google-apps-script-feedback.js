// =============================================================
// GOOGLE APPS SCRIPT — Subscription + Feedback for AI Career Transition
// =============================================================
//
// HANDLES: Email subscription (blog) + Feedback form + Feature request + Contact form
//
// TO UPDATE YOUR EXISTING SCRIPT:
// 1. Go to https://script.google.com and open "AI Career Transition Subscribers"
// 2. Select ALL code and DELETE it
// 3. Paste THIS ENTIRE FILE
// 4. Save
// 5. Deploy -> Manage deployments -> Edit (pencil) -> Version: New version -> Deploy
//
// Feedback/Feature/Contact go to "AI Career Transition - Feedback" spreadsheet
// =============================================================

var SUBSCRIBERS_SHEET = 'Subscribers';
var SUBSCRIBERS_SS_NAME = 'AI Career Transition - Email Subscribers';
var FEEDBACK_SS_NAME = 'AI Career Transition - Feedback';
var FEEDBACK_SHEET = 'Submissions';

function getOrCreateFeedbackSpreadsheet() {
  var files = DriveApp.getFilesByName(FEEDBACK_SS_NAME);
  if (files.hasNext()) {
    var ss = SpreadsheetApp.open(files.next());
    var sheet = ss.getSheetByName(FEEDBACK_SHEET);
    if (!sheet) {
      sheet = ss.insertSheet(FEEDBACK_SHEET);
      sheet.appendRow(['Form Type', 'Name', 'Email', 'Subject/Title', 'Category/Role', 'Message', 'Timestamp']);
      sheet.getRange('1:1').setFontWeight('bold');
    }
    return ss;
  }
  var ss = SpreadsheetApp.create(FEEDBACK_SS_NAME);
  var sheet = ss.getActiveSheet();
  sheet.setName(FEEDBACK_SHEET);
  sheet.appendRow(['Form Type', 'Name', 'Email', 'Subject/Title', 'Category/Role', 'Message', 'Timestamp']);
  sheet.getRange('1:1').setFontWeight('bold');
  sheet.setColumnWidth(6, 350);
  return ss;
}

function getOrCreateSubscribersSpreadsheet() {
  var files = DriveApp.getFilesByName(SUBSCRIBERS_SS_NAME);
  if (files.hasNext()) {
    return SpreadsheetApp.open(files.next());
  }
  var ss = SpreadsheetApp.create(SUBSCRIBERS_SS_NAME);
  var sheet = ss.getActiveSheet();
  sheet.setName(SUBSCRIBERS_SHEET);
  sheet.appendRow(['Email', 'Date Subscribed', 'Source Page']);
  sheet.getRange('1:1').setFontWeight('bold');
  return ss;
}

function processSubscription(email, source) {
  if (!email || email.indexOf('@') === -1 || email.indexOf('.') === -1) {
    return sendResponse('error', 'Please enter a valid email address.');
  }
  var ss = getOrCreateSubscribersSpreadsheet();
  var sheet = ss.getSheetByName(SUBSCRIBERS_SHEET);
  if (!sheet) {
    sheet = ss.insertSheet(SUBSCRIBERS_SHEET);
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

function truncate(str, maxLen) {
  if (!str || typeof str !== 'string') return '';
  if (str.length <= maxLen) return str;
  return str.substring(0, maxLen) + '...';
}

function processFeedbackForm(p) {
  var formType = (p.form || 'feedback').toLowerCase();
  if (formType !== 'feedback' && formType !== 'feature' && formType !== 'contact') {
    return sendResponse('error', 'Invalid form type.');
  }
  var name = (p.name || '').trim();
  var email = (p.email || '').trim();
  var subject = (p.subject || p.title || p.feedback_type || '').trim();
  var category = (p.category || p.role || '').trim();
  var message = truncate((p.message || p.description || '').trim(), 800);
  if (!message) {
    return sendResponse('error', 'Message is required.');
  }
  var ss = getOrCreateFeedbackSpreadsheet();
  var sheet = ss.getSheetByName(FEEDBACK_SHEET);
  var now = new Date();
  var dateStr = Utilities.formatDate(now, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss');
  sheet.appendRow([formType, name, email, subject, category, message, dateStr]);
  return sendResponse('success', 'Thank you! Your submission has been received.');
}

function doGet(e) {
  try {
    var p = e.parameter || {};
    var form = (p.form || '').toLowerCase();
    if (form === 'feedback' || form === 'feature' || form === 'contact') {
      return processFeedbackForm(p);
    }
    var email = (p.email || '').trim().toLowerCase();
    var source = p.source || 'blog.html';
    if (!email) {
      return sendResponse('ok', 'Endpoint is working.');
    }
    return processSubscription(email, source);
  } catch (err) {
    return sendResponse('error', 'Something went wrong. Please try again.');
  }
}

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var form = (data.form || '').toLowerCase();
    if (form === 'feedback' || form === 'feature' || form === 'contact') {
      return processFeedbackForm(data);
    }
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
