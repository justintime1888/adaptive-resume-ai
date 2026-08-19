/**
 * Google Apps Script for Adaptive Resume & Job Tracker
 * Paste this into Google Sheets: Extensions -> Apps Script
 * Deploy -> New Deployment -> Web App (Execute as: Me, Who has access: Anyone)
 * Copy the Web App URL and set GOOGLE_SHEETS_WEBHOOK_URL in your .env file!
 */

function doPost(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var data = JSON.parse(e.postData.contents);
    
    if (!data || data.length === 0) {
      return ContentService.createTextOutput(JSON.stringify({ status: "empty" })).setMimeType(ContentService.MimeType.JSON);
    }
    
    sheet.clearContents();
    
    var range = sheet.getRange(1, 1, data.length, data[0].length);
    range.setValues(data);
    
    // Formatting Header
    var header = sheet.getRange(1, 1, 1, data[0].length);
    header.setFontWeight("bold");
    header.setBackground("#0F2043");
    header.setFontColor("#FFFFFF");
    sheet.setFrozenRows(1);
    sheet.autoResizeColumns(1, data[0].length);
    
    return ContentService.createTextOutput(JSON.stringify({ status: "success", rows: data.length })).setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ status: "error", message: err.toString() })).setMimeType(ContentService.MimeType.JSON);
  }
}