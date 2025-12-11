VENDING_DRINKS = {
  child: {
    cold: ["warm milk", "hot chocolate"],
    moderate: ["water", "fruit smoothies"],
    hot: ["juice", "flavored milk"],
  },
  teen: {
    cold: ["hot chocolate", "tea"],
    moderate: ["energy drinks", "flavored water"],
    hot: ["soda", "iced tea"],
  },
  adult: {
    cold: ["coffee", "tea"],
    moderate: ["herbal tea", "sparkling water"],
    hot: ["iced coffee", "soft drinks"],
  },
  senior: {
    cold: ["herbal tea", "warm water"],
    moderate: ["green tea", "fruit juice"],
    hot: ["water", "iced tea"],
  },
};

const webSocket = new WebSocket("/vending-machine/full-system?mode=4");
const container = document.querySelector(".right");

const InboundInstruction = Object.freeze({
  PROCESSING_USER: "PROCESSING USER",
  DISPLAY_DRINKS: "DISPLAY DRINKS",
  PREPARING_DRINK: "PREPARING DRINK",
  DRINK_READY: "DRINK READY",
  RESET: "RESET",
});

const OutboundInstruction = Object.freeze({
  START_ORDER: "START ORDER",
  VEND: "VEND",
  TAKE_DRINK: "TAKE DRINK",
  CANCEL: "CANCEL",
});

webSocket.addEventListener("open", () => {
  webSocket.send("Start");
  console.log("Start");
});

webSocket.addEventListener("close", () => {});

webSocket.addEventListener("message", (event) => {
  const vending = document.createElement("div");
  const buyOrCancel = document.createElement("div");
  const takeDrink = document.createElement("div");

  vending.className = "vending";
  buyOrCancel.className = "button-area";

  let message = JSON.parse(event.data);
  // let message = {
  //   type: InboundInstruction.DRINK_READY,
  //   detectionData: {
  //     age: 28,
  //     ageGroup: "adult",
  //     weather: "moderate",
  //   },
  // };

  if (message.type == InboundInstruction.RESET) {
    const btnOrder = document.createElement("input");
    btnOrder.type = "button";
    btnOrder.value = "ORDER";
    btnOrder.className = "order";

    btnOrder.addEventListener("click", () => {
      webSocket.send(JSON.stringify({ type: OutboundInstruction.START_ORDER }));
    });

    vending.appendChild(btnOrder);
  } else if (message.type == InboundInstruction.PROCESSING_USER) {
    const span = document.createElement("span");
    span.textContent = "Processing User...";

    vending.appendChild(span);
  } else if (message.type == InboundInstruction.DISPLAY_DRINKS) {
    takeDrink.style.display = "none";
    buyOrCancel.style.diisplay = "block";

    detectionData = message.detectionData;

    const age = document.createElement("span");
    age.textContent = `Age: ${detectionData.age}`;
    vending.appendChild(age);

    const ageGroup = document.createElement("span");
    ageGroup.textContent = `Age Group: ${detectionData.ageGroup}`;
    vending.appendChild(ageGroup);

    const weather = document.createElement("span");
    weather.textContent = `Weather: ${detectionData.weather}`;
    vending.appendChild(weather);

    const drinks = document.createElement("span");
    drinks.textContent = "SUGGESTED DRINKS:";
    vending.appendChild(drinks);

    for (let drink of VENDING_DRINKS[detectionData.ageGroup][
      detectionData.weather
    ]) {
      const label = document.createElement("label");

      const input = document.createElement("input");
      input.type = "radio";
      input.name = "drink";
      input.className = "drink";
      input.value = drink;

      label.appendChild(input);
      label.append(drink);
      vending.appendChild(label);
      vending.appendChild(document.createElement("br")); // Line break after each label
    }

    const btnBuy = document.createElement("input");
    btnBuy.type = "button";
    btnBuy.value = "BUY";
    btnBuy.className = "buy";

    btnBuy.addEventListener("click", () => {
      let drink_options = document.getElementsByClassName("drink");
      let transactionData = {
        age: detectionData.age,
        ageGroup: detectionData.ageGroup,
        weather: detectionData.weather,
      };

      for (let index = 0; index < drink_options.length; index++) {
        if (drink_options[index].checked) {
          transactionData["drink"] = drink_options[index].value;
        }
      }

      webSocket.send(
        JSON.stringify({
          type: OutboundInstruction.VEND,
          transactionData: transactionData,
        })
      );
    });

    buyOrCancel.appendChild(btnBuy);

    const btnCancel = document.createElement("input");
    btnCancel.type = "button";
    btnCancel.value = "CANCEL";

    btnCancel.addEventListener("click", () => {
      webSocket.send(JSON.stringify({ type: OutboundInstruction.CANCEL }));
    });

    buyOrCancel.appendChild(btnCancel);

    vending.appendChild(buyOrCancel);
  } else if (message.type == InboundInstruction.PREPARING_DRINK) {
    const span = document.createElement("span");
    span.textContent = "Preparing Drink...";

    vending.appendChild(span);
  } else if (message.type == InboundInstruction.DRINK_READY) {
    const span = document.createElement("span");
    span.textContent = "Your drink is ready.";

    vending.appendChild(span);

    const btnTake = document.createElement("input");
    btnTake.type = "button";
    btnTake.value = "TAKE";

    btnTake.addEventListener("click", () => {
      webSocket.send(JSON.stringify({ type: OutboundInstruction.TAKE_DRINK }));
    });

    takeDrink.appendChild(btnTake);
    vending.appendChild(takeDrink);
  }

  container.replaceChildren(vending);
});
