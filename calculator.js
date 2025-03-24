function calculate() {
  const display = document.getElementById("display");
  let expression = display.value;

  try {
    let result = eval(expression); // Note: eval() can be dangerous if used with untrusted input

    if (isNaN(result) || !isFinite(result)) {
      display.value = "Error";
    } else {
      display.value = result;
    }
  } catch (error) {
    display.value = "Error";
  }
}

function appendToDisplay(value) {
  document.getElementById("display").value += value;
}

function clearDisplay() {
  document.getElementById("display").value = "";
}

function deleteLast() {

  const display = document.getElementById("display");
  display.value = display.value.slice(0, -1);

}

// HTML (example)

/*
<input type="text" id="display" readonly>
<br>
<button onclick="appendToDisplay('7')">7</button>
<button onclick="appendToDisplay('8')">8</button>
<button onclick="appendToDisplay('9')">9</button>
<button onclick="appendToDisplay('+')">+</button>
<br>
<button onclick="appendToDisplay('4')">4</button>
<button onclick="appendToDisplay('5')">5</button>
<button onclick="appendToDisplay('6')">6</button>
<button onclick="appendToDisplay('-')">-</button>
<br>
<button onclick="appendToDisplay('1')">1</button>
<button onclick="appendToDisplay('2')">2</button>
<button onclick="appendToDisplay('3')">3</button>
<button onclick="appendToDisplay('*')">*</button>
<br>
<button onclick="appendToDisplay('0')">0</button>
<button onclick="appendToDisplay('.')">.</button>
<button onclick="calculate()">=</button>
<button onclick="appendToDisplay('/')">/</button>
<br>
<button onclick="clearDisplay()">C</button>
<button onclick="deleteLast()">DEL</button>

*/
