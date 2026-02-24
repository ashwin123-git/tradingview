
let userCurrency="USD";
fetch("/api/user_currency").then(r=>r.json()).then(d=>userCurrency=d.currency);

async function convert(v){
 if(userCurrency==="USD") return v.toFixed(2);
 try {
   let r = await fetch(`/api/convert/${v}/${userCurrency}`);
   if (!r.ok) throw new Error('bad status');
   let d = await r.json();
   return parseFloat(d.converted).toFixed(2);
 } catch (e) {
   console.warn('conversion failed', e);
   return v.toFixed(2);
 }
}

async function stocks(){
 try {
   let resp=await fetch("/api/stocks").then(r=>r.json());
   let data = resp.stocks || {};
   let source = resp.source || "";
   let c=document.getElementById("stockCards");
   c.innerHTML="";
   if(!data || Object.keys(data).length===0){
     c.innerHTML = `<p class="text-center text-red-600">Live stock data unavailable – the market API could not be reached. Crypto below still loads normally.</p>`;
     return;
   }
   // show a little badge if data not fresh
   if(source && source!="live"){
     c.innerHTML += `<p class="text-sm text-yellow-600 mb-2">Showing ${source} data</p>`;
   }
   for(let s in data){
     let st=data[s];
     let price=await convert(st.price);
     let changeClass = st.change>=0 ? 'text-green-600' : 'text-red-600';
     let changeSign = st.change>=0 ? '+' : '';
     c.innerHTML+=`
     <a href="/stock/${s}" class="bg-white p-4 rounded shadow hover:shadow-lg transition-transform transform hover:scale-105 block">
       <h3 class="font-bold text-lg">${s}</h3>
       <p class="text-xl">${price} USD</p>
       <p class="${changeClass}">${changeSign}${st.change}%</p>
       <canvas id="g${s}" class="w-full" height="40"></canvas>
     </a>`;
     new Chart(document.getElementById("g"+s),{
      type:"line",
      data:{labels:st.history,datasets:[{data:st.history,borderWidth:1,pointRadius:0,backgroundColor:'rgba(99,102,241,0.2)',borderColor:'rgba(99,102,241,1)'}]},
      options:{plugins:{legend:{display:false}},scales:{x:{display:false},y:{display:false}}}
     });
   }
 } catch(e){
   // ensure crypto still loads
   console.error("error rendering stocks", e);
   document.getElementById("stockCards").innerHTML = `<p class="text-center text-red-600">Unable to render stock cards due to an error. Crypto below still available.</p>`;
 }
}

async function crypto(){
 try {
   let data=await fetch("/api/currencies").then(r=>r.json());
   let c=document.getElementById("cryptoCards");
   c.innerHTML="";
   for(let s in data){
     let st=data[s];
     let price=await convert(st.usd);
     c.innerHTML+=`
     <div class="bg-white p-4 rounded shadow">
     <h3 class="font-bold">${s}</h3>
     <p>${price} ${userCurrency}</p>
     <canvas id="c${s}" height="40"></canvas>
     </div>`;
     new Chart(document.getElementById("c"+s),{
      type:"line",
      data:{labels:st.history,datasets:[{data:st.history,borderWidth:1,pointRadius:0}]},
      options:{plugins:{legend:{display:false}},scales:{x:{display:false},y:{display:false}}}
     });
   }
 } catch(e){
   console.error("crypto render failed", e);
   document.getElementById("cryptoCards").innerHTML = `<p class="text-center text-red-600">Unable to load crypto data.</p>`;
 }
}

stocks();crypto();
setInterval(()=>{stocks();crypto()},60000);
