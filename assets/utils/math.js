export const roundToDecimal = (number, decimalPlaces) => {
  var factor = Math.pow(10, decimalPlaces);
  return Math.round(number * factor) / factor;
};

export const isRoundedEqual = (num1, num2, decimalPlaces) => {
  return (
    roundToDecimal(num1, decimalPlaces) === roundToDecimal(num2, decimalPlaces)
  );
};
