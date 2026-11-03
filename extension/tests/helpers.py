"""Real extension + CDP instrumentation, with no production test hooks."""
import hashlib
import json
import os
import time
from pathlib import Path

EXT = Path(os.environ.get('PARIVIEW_EXTENSION', Path(__file__).resolve().parents[1])).resolve()
EXT_ID = ''.join(chr(97 + int(c, 16)) for c in hashlib.sha256(str(EXT).encode()).hexdigest()[:32])


def launch(p, profile):
    return p.chromium.launch_persistent_context(str(profile), headless=True, channel='chromium', viewport={'width': 1280, 'height': 900}, args=[f'--disable-extensions-except={EXT}', f'--load-extension={EXT}'])


def popup(context):
    pop = context.new_page()
    pop.goto(f'chrome-extension://{EXT_ID}/popup.html')
    pop.wait_for_function("typeof requestStatus === 'function'")
    return pop


def save(pop, **settings):
    pop.evaluate('(settings) => chrome.storage.local.set({profile:{settings,updatedAt:new Date().toISOString()}})', settings)
    pop.wait_for_timeout(150)


def inspect(pop, page):
    page.bring_to_front()
    pop.evaluate('async () => requestStatus((await chrome.tabs.query({active:true,currentWindow:true}))[0].id)')
    pop.wait_for_timeout(300)
    return pop.evaluate("({state:document.querySelector('.status').dataset.state,title:document.querySelector('#status-title').textContent,detail:document.querySelector('#status-detail').textContent,frames:[...frames.values()]})")


def world(context, page):
    cd = context.new_cdp_session(page)
    contexts = []
    cd.on('Runtime.executionContextCreated', lambda e: contexts.append(e['context']))
    cd.send('Runtime.enable')
    for _ in range(50):
        matches = [c for c in contexts if c['origin'] == f'chrome-extension://{EXT_ID}']
        if matches:
            return cd, matches[0]['id']
        page.wait_for_timeout(100)
    raise AssertionError('Extension isolated world not found')


def evaluate(w, expression):
    cd, context_id = w
    result = cd.send('Runtime.evaluate', {'contextId': context_id, 'expression': expression, 'returnByValue': True, 'awaitPromise': True})
    if 'exceptionDetails' in result:
        raise AssertionError(result['exceptionDetails'].get('text', 'isolated-world exception'))
    return result['result'].get('value')


# Tap the actual input and destination-bound signal in the extension's isolated
# world. No replacement audio or product status is injected. Original methods
# still run; the analysers have no output connection and do not alter playback.
INSTRUMENT = r'''(() => {
  const qa = globalThis.__pvQA = { nodes: [], links: [] };
  for (const method of ['createGain','createBiquadFilter','createDynamicsCompressor','createMediaElementSource']) {
    const original = AudioContext.prototype[method];
    AudioContext.prototype[method] = function(...args) {
      const node = original.apply(this,args);
      qa.context = this;
      qa.nodes.push({type:method,node});
      if (method === 'createMediaElementSource') {
        qa.source = node;
        qa.input = this.createAnalyser(); qa.input.fftSize = 2048;
      }
      return node;
    };
  }
  const connect = AudioNode.prototype.connect;
  const disconnect = AudioNode.prototype.disconnect;
  AudioNode.prototype.connect = function(...args) {
    const result = connect.apply(this,args);
    qa.links.push([this,args[0]]);
    if (args[0] === this.context.destination) {
      qa.output ||= this.context.createAnalyser(); qa.output.fftSize = 2048;
      connect.call(this,qa.output);
    }
    if (this === qa.source && qa.input) connect.call(this,qa.input);
    return result;
  };
  AudioNode.prototype.disconnect = function(...args) {
    const result = disconnect.apply(this,args);
    qa.links = qa.links.filter(([from,to]) => from !== this || (args.length && to !== args[0]));
    return result;
  };
  qa.measure = async () => {
    if (!qa.input || !qa.output) return {inputRMS:0,outputRMS:0};
    const a = new Float32Array(2048), b = new Float32Array(2048);
    let input = 0, output = 0;
    for (let n = 0; n < 50; n++) {
      qa.input.getFloatTimeDomainData(a); qa.output.getFloatTimeDomainData(b);
      for (let i = 0; i < a.length; i++) { input += a[i]*a[i]; output += b[i]*b[i]; }
      await new Promise(r => setTimeout(r,20));
    }
    return {inputRMS:Math.sqrt(input/(50*2048)),outputRMS:Math.sqrt(output/(50*2048)),ratio:Math.sqrt(output/input)};
  };
  qa.parameters = () => ({
    context:qa.context?.state,
    gain:qa.nodes.filter(n=>n.type==='createGain').map(n=>n.node.gain.value),
    filters:qa.nodes.filter(n=>n.type==='createBiquadFilter').map(n=>({type:n.node.type,frequency:n.node.frequency.value,gain:n.node.gain.value})),
    compression:qa.nodes.filter(n=>n.type==='createDynamicsCompressor').map(n=>({threshold:n.node.threshold.value,ratio:n.node.ratio.value})),
    sources:qa.nodes.filter(n=>n.type==='createMediaElementSource').length,
    bypass:qa.links.some(([from,to])=>from===qa.source && to===qa.context.destination),
  });
})()'''


def instrument(context, page):
    w = world(context, page)
    evaluate(w, INSTRUMENT)
    return w


def check(results, name, condition, detail=None):
    results[name] = {'passed': bool(condition)}
    if detail is not None:
        results[name]['detail'] = detail
    print(json.dumps({name: results[name]}, ensure_ascii=False), flush=True)
    if not condition:
        raise AssertionError(name)
