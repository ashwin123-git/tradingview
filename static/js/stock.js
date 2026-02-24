
// always show USD
async function conv(v){
  return v.toFixed(2);
}

async function run(){
  // symbol is stored on body to avoid issues with trailing slashes
  let sym=document.body.dataset.symbol || location.pathname.split("/").filter(Boolean).pop();
  let resp=await fetch("/api/stocks").then(r=>r.json());
  let data=resp.stocks||{};
  let s=data[sym];
  let infoEl=document.getElementById("stockInfo");
  if(!s){
    infoEl.innerHTML = `<p class="text-red-600">Stock '${sym}' not found.</p>`;
    return;
  }
  let price=await conv(s.price);
  let changeClass = s.change>=0 ? 'text-green-600' : 'text-red-600';
  let changeSign = s.change>=0 ? '+' : '';

  infoEl.innerHTML=
  `<h2 class="text-xl font-bold">${price} USD</h2>
   <p class="${changeClass}">${changeSign}${s.change}%</p>`;

  new Chart(document.getElementById("stockChart"),{
    type:"line",
    data:{labels:s.history,datasets:[{data:s.history,borderWidth:2,backgroundColor:'rgba(59,130,246,0.2)',borderColor:'rgba(59,130,246,1)'}]},
    options:{plugins:{legend:{display:false}}}
  });
}
run();
