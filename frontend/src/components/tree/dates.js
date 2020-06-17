let today = new Date();
let thisMonth = today.getMonth();
let thisYear = today.getFullYear();;

let monthData = [];
let monthLabels = [];
let lastDaysData = [];
let maxMonthsShown = 12;
let daysInMonths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
let months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function leapYear(year) {
    return ((year % 4 == 0) && (year % 100 != 0)) || (year % 400 == 0);
}

for (let i = (maxMonthsShown - 1); i >= 0; i--) {
    monthLabels[i] = months[thisMonth];
    monthData[i] = thisYear + '-' + (thisMonth + 1);

    if (thisMonth == 1 && leapYear(thisYear)) {
        lastDaysData[i] = 29;
    } else {
        lastDaysData[i] = daysInMonths[thisMonth];
    }

    if (thisMonth == 0) {
        thisMonth = 11;
        thisYear--;
    } else {
        thisMonth--;
    }
}

export {monthData, monthLabels, lastDaysData, maxMonthsShown};