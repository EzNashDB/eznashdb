export const hasHebrew = (inputStr) => {
  const hebrewChars = /[אבגדהוזחטיךכלםמןנסעףפץצקרשת]/;
  return hebrewChars.test(inputStr);
};
