/**
 * Action Visualizer for Monitor
 * 
 * Renders SVG overlays on screenshots to visualize agent actions.
 * Ported from trajectory_visualizer with adaptations for monitor's data format.
 * 
 * Supports: pyautogui-style actions (click, drag, scroll, type, hotkey, etc.)
 * and structured action objects {type, coordinate, ...}.
 */

class ActionVisualizer {
    constructor(overlay, img, wrapper) {
        this.overlay = overlay;
        this.screenshotImg = img;
        this.screenshotWrapper = wrapper;
        
        this.colors = {
            click: '#ef4444',
            drag: '#8b5cf6',
            scroll: '#3b82f6',
            mouse_move: '#f59e0b',
            type: '#22c55e',
            hotkey: '#f59e0b',
            wait: '#64748b',
            finished: '#22c55e'
        };
        
        this.clickActions = [
            'left_click', 'right_click', 'middle_click',
            'double_click', 'triple_click', 'click'
        ];
        
        this.naturalWidth = 0;
        this.naturalHeight = 0;
        this.displayWidth = 0;
        this.displayHeight = 0;
    }
    
    updateOverlayDimensions() {
        if (!this.screenshotImg || this.screenshotImg.style.display === 'none') return;
        
        const rect = this.screenshotImg.getBoundingClientRect();
        this.displayWidth = rect.width;
        this.displayHeight = rect.height;
        this.naturalWidth = this.screenshotImg.naturalWidth;
        this.naturalHeight = this.screenshotImg.naturalHeight;
        
        if (!this.naturalWidth || !this.naturalHeight) return;
        
        this.overlay.setAttribute('viewBox', `0 0 ${this.naturalWidth} ${this.naturalHeight}`);
        this.overlay.style.width = `${this.displayWidth}px`;
        this.overlay.style.height = `${this.displayHeight}px`;
        
        const wrapperRect = this.screenshotWrapper.getBoundingClientRect();
        const imgRect = this.screenshotImg.getBoundingClientRect();
        this.overlay.style.left = `${imgRect.left - wrapperRect.left}px`;
        this.overlay.style.top = `${imgRect.top - wrapperRect.top}px`;
    }
    
    clear() {
        this.overlay.innerHTML = '';
    }
    
    createSVGElement(tag, attrs = {}) {
        const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
        for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
        return el;
    }

    /**
     * Extract the full argument string from a pyautogui call, handling
     * triple-quoted strings, nested parentheses, and regular strings.
     * Returns {fn, argsStr, endIndex} or null if no match.
     */
    _extractPyAutoGUICall(line) {
        const prefixMatch = line.match(/pyautogui\.(\w+)\(/);
        if (!prefixMatch) return null;
        const fn = prefixMatch[1];
        const startIdx = prefixMatch.index + prefixMatch[0].length;
        let depth = 1;
        let i = startIdx;
        while (i < line.length && depth > 0) {
            // Skip triple-quoted strings
            if (line.substring(i, i + 3) === '"""') {
                i += 3;
                const end = line.indexOf('"""', i);
                i = end === -1 ? line.length : end + 3;
                continue;
            }
            if (line.substring(i, i + 3) === "'''") {
                i += 3;
                const end = line.indexOf("'''", i);
                i = end === -1 ? line.length : end + 3;
                continue;
            }
            // Skip single/double quoted strings
            if (line[i] === '"' || line[i] === "'") {
                const q = line[i];
                i++;
                while (i < line.length && line[i] !== q) {
                    if (line[i] === '\\') i++; // skip escaped char
                    i++;
                }
                i++; // skip closing quote
                continue;
            }
            if (line[i] === '(') depth++;
            else if (line[i] === ')') depth--;
            if (depth > 0) i++;
            else break; // found matching closing paren
        }
        if (depth !== 0) return null;
        const argsStr = line.substring(startIdx, i);
        return { fn, argsStr, endIndex: i + 1 };
    }

    /**
     * Parse a pyautogui action string into structured action objects.
     * e.g. "pyautogui.click(422, 265)" -> [{type:'click', coordinate:[422,265]}]
     */
    parsePyAutoGUIAction(actionStr) {
        if (!actionStr || typeof actionStr !== 'string') return [];
        const s = actionStr.trim();
        const actions = [];

        // Terminal actions
        if (s === 'DONE') return [{type: 'finished', status: 'success'}];
        if (s === 'FAIL') return [{type: 'finished', status: 'failure'}];
        if (s === 'WAIT') return [{type: 'wait', time: 1}];

        // Split multi-line actions
        const lines = s.split('\n').map(l => l.trim()).filter(Boolean);
        for (const line of lines) {
            const parsed = this._extractPyAutoGUICall(line);
            if (!parsed) continue;
            const fn = parsed.fn;
            const argsStr = parsed.argsStr;
            
            if (fn === 'click') {
                const coords = argsStr.match(/(\d+)\s*,\s*(\d+)/);
                if (coords) actions.push({type: 'left_click', coordinate: [parseInt(coords[1]), parseInt(coords[2])]});
            } else if (fn === 'rightClick') {
                const coords = argsStr.match(/(\d+)\s*,\s*(\d+)/);
                if (coords) actions.push({type: 'right_click', coordinate: [parseInt(coords[1]), parseInt(coords[2])]});
            } else if (fn === 'doubleClick') {
                const coords = argsStr.match(/(\d+)\s*,\s*(\d+)/);
                if (coords) actions.push({type: 'double_click', coordinate: [parseInt(coords[1]), parseInt(coords[2])]});
            } else if (fn === 'tripleClick') {
                const coords = argsStr.match(/(\d+)\s*,\s*(\d+)/);
                if (coords) actions.push({type: 'triple_click', coordinate: [parseInt(coords[1]), parseInt(coords[2])]});
            } else if (fn === 'middleClick') {
                const coords = argsStr.match(/(\d+)\s*,\s*(\d+)/);
                if (coords) actions.push({type: 'middle_click', coordinate: [parseInt(coords[1]), parseInt(coords[2])]});
            } else if (fn === 'moveTo') {
                const coords = argsStr.match(/(\d+)\s*,\s*(\d+)/);
                if (coords) actions.push({type: 'mouse_move', coordinate: [parseInt(coords[1]), parseInt(coords[2])]});
            } else if (fn === 'dragTo') {
                const coords = argsStr.match(/(\d+)\s*,\s*(\d+)/);
                if (coords) actions.push({type: 'drag', coordinate: [parseInt(coords[1]), parseInt(coords[2])]});
            } else if (fn === 'scroll') {
                const val = argsStr.match(/-?\d+/);
                if (val) actions.push({type: 'scroll', pixels: parseInt(val[0])});
            } else if (fn === 'typewrite') {
                const tm3 = argsStr.match(/"""([\s\S]*?)"""|'''([\s\S]*?)'''/);
                const tm1 = !tm3 ? argsStr.match(/['"](.*?)['"]/) : null;
                const text = tm3 ? (tm3[1] != null ? tm3[1] : tm3[2]) : (tm1 ? tm1[1] : argsStr);
                actions.push({type: 'type', text: text});
            } else if (fn === 'press') {
                const km = argsStr.match(/['"](.*?)['"]/);
                actions.push({type: 'press', keys: [km ? km[1] : argsStr]});
            } else if (fn === 'hotkey') {
                const keys = argsStr.replace(/['"]/g, '').split(',').map(k => k.trim()).filter(Boolean);
                actions.push({type: 'hotkey', keys: keys});
            } else if (fn === 'keyDown') {
                const km = argsStr.match(/['"](.*?)['"]/);
                actions.push({type: 'key_down', keys: [km ? km[1] : argsStr]});
            } else if (fn === 'keyUp') {
                const km = argsStr.match(/['"](.*?)['"]/);
                actions.push({type: 'key_up', keys: [km ? km[1] : argsStr]});
            }
        }
        return actions;
    }
    
    /**
     * Merge consecutive single-char press actions into type actions.
     * e.g. press('h'), press('i') -> type('hi')
     */
    mergeConsecutivePress(actions) {
        const merged = [];
        let pressBuffer = [];
        
        function flushPressBuffer() {
            if (pressBuffer.length === 0) return;
            if (pressBuffer.length >= 2 && pressBuffer.every(k => k.length === 1)) {
                merged.push({type: 'type', text: pressBuffer.join('')});
            } else if (pressBuffer.length >= 2) {
                merged.push({type: 'hotkey', keys: pressBuffer});
            } else {
                merged.push({type: 'press', keys: pressBuffer});
            }
            pressBuffer = [];
        }
        
        for (const action of actions) {
            if (action.type === 'press' && action.keys && action.keys.length === 1) {
                pressBuffer.push(action.keys[0]);
            } else {
                flushPressBuffer();
                merged.push(action);
            }
        }
        flushPressBuffer();
        return merged;
    }

    /**
     * Visualize actions on the screenshot.
     * @param {Array|Object|string} input - Structured action(s), or raw pyautogui action string
     */
    visualize(input) {
        this.clear();
        
        let actions = [];
        if (typeof input === 'string') {
            actions = this.parsePyAutoGUIAction(input);
        } else if (Array.isArray(input)) {
            actions = input;
        } else if (input && input.type) {
            actions = [input];
        }
        
        if (actions.length === 0) return;
        
        // Merge consecutive single-char press into type
        actions = this.mergeConsecutivePress(actions);
        
        this.updateOverlayDimensions();
        
        // Track vertical offset for non-coordinate indicators
        this._nonCoordYOffset = 0;
        
        let movetoCoord = null;
        actions.forEach((action, idx) => {
            if (!action || !action.type) return;
            if (action.type === 'moveto' || action.type === 'mouse_move') {
                movetoCoord = action.coordinate;
                this.visualizeAction(action);
            } else if (action.type === 'drag') {
                this.drawDrag(action.coordinate, movetoCoord);
                movetoCoord = null;
            } else {
                this.visualizeAction(action);
            }
        });
    }
    
    visualizeAction(action) {
        const t = action.type;
        if (this.clickActions.includes(t)) {
            this.drawClick(action.coordinate, t);
        } else if (t === 'drag') {
            this.drawDrag(action.coordinate);
        } else if (t === 'mouse_move' || t === 'moveto') {
            this.drawMouseMove(action.coordinate, t);
        } else if (t === 'scroll') {
            this.drawScroll(action.pixels);
        } else if (t === 'type') {
            this.drawTypeIndicator(action.text);
        } else if (['hotkey', 'press', 'key_down', 'key_up'].includes(t)) {
            this.drawHotkeyIndicator(action.keys, t);
        } else if (t === 'wait') {
            this.drawWaitIndicator(action.time);
        } else if (t === 'finished') {
            this.drawFinishedIndicator(action.status);
        }
    }
    
    drawClick(coordinate, actionType) {
        if (!coordinate || coordinate.length < 2) return;
        const [x, y] = coordinate;
        const color = this.colors.click;
        const g = this.createSVGElement('g', {class: 'click-marker'});
        
        const outer = this.createSVGElement('circle', {cx:x, cy:y, r:30, fill:'none', stroke:color, 'stroke-width':3, opacity:0.5});
        outer.innerHTML = `<animate attributeName="r" from="20" to="40" dur="1s" repeatCount="indefinite"/>
            <animate attributeName="opacity" from="0.8" to="0" dur="1s" repeatCount="indefinite"/>`;
        g.appendChild(outer);
        g.appendChild(this.createSVGElement('circle', {cx:x, cy:y, r:12, fill:color, opacity:0.9}));
        g.appendChild(this.createSVGElement('circle', {cx:x, cy:y, r:4, fill:'white'}));
        
        const tw = this.getTextWidth(actionType);
        g.appendChild(this.createSVGElement('rect', {x:x+20, y:y-12, width:tw+16, height:24, rx:4, fill:color}));
        const label = this.createSVGElement('text', {x:x+28, y:y+4, fill:'white', 'font-size':14, 'font-weight':'bold', 'font-family':'Arial, sans-serif'});
        label.textContent = actionType;
        g.appendChild(label);
        
        const coordLabel = this.createSVGElement('text', {x:x+28, y:y+28, fill:color, 'font-size':12, 'font-family':'Monaco, monospace'});
        coordLabel.textContent = `(${x}, ${y})`;
        g.appendChild(coordLabel);
        
        this.overlay.appendChild(g);
    }
    
    drawDrag(targetCoord, startCoord = null) {
        if (!targetCoord || targetCoord.length < 2) return;
        const [tx, ty] = targetCoord;
        const color = this.colors.drag;
        let sx = startCoord ? startCoord[0] : this.naturalWidth / 2;
        let sy = startCoord ? startCoord[1] : this.naturalHeight / 2;
        
        const g = this.createSVGElement('g', {class: 'drag-marker'});
        const defs = this.createSVGElement('defs');
        const marker = this.createSVGElement('marker', {id:'drag-arrow-'+Date.now(), markerWidth:10, markerHeight:10, refX:8, refY:5, orient:'auto'});
        marker.appendChild(this.createSVGElement('path', {d:'M 0 0 L 10 5 L 0 10 z', fill:color}));
        defs.appendChild(marker);
        g.appendChild(defs);
        
        g.appendChild(this.createSVGElement('line', {x1:sx, y1:sy, x2:tx, y2:ty, stroke:color, 'stroke-width':4, 'stroke-dasharray':'10,5', 'marker-end':`url(#${marker.id})`, opacity:0.8}));
        g.appendChild(this.createSVGElement('circle', {cx:sx, cy:sy, r:8, fill:color, opacity:0.5}));
        g.appendChild(this.createSVGElement('circle', {cx:tx, cy:ty, r:12, fill:color, opacity:0.9}));
        g.appendChild(this.createSVGElement('circle', {cx:tx, cy:ty, r:4, fill:'white'}));
        
        const label = this.createSVGElement('text', {x:tx+20, y:ty+5, fill:color, 'font-size':14, 'font-weight':'bold', 'font-family':'Arial, sans-serif'});
        label.textContent = `drag (${sx}, ${sy}) → (${tx}, ${ty})`;
        g.appendChild(label);
        this.overlay.appendChild(g);
    }
    
    drawMouseMove(coordinate, actionType = 'mouse_move') {
        if (!coordinate || coordinate.length < 2) return;
        const [x, y] = coordinate;
        const color = this.colors.mouse_move;
        const g = this.createSVGElement('g', {class: 'mouse-move-marker'});
        g.appendChild(this.createSVGElement('path', {
            d: `M ${x} ${y} L ${x+20} ${y+25} L ${x+8} ${y+25} L ${x+12} ${y+35} L ${x+5} ${y+37} L ${x} ${y+27} L ${x-8} ${y+27} Z`,
            fill: color, stroke: 'white', 'stroke-width': 2, opacity: 0.9
        }));
        const label = this.createSVGElement('text', {x:x+25, y:y+5, fill:color, 'font-size':14, 'font-weight':'bold', 'font-family':'Arial, sans-serif'});
        label.textContent = `${actionType} (${x}, ${y})`;
        g.appendChild(label);
        this.overlay.appendChild(g);
    }
    
    drawScroll(pixels) {
        const color = this.colors.scroll;
        const isUp = pixels > 0;
        const yOff = this._nonCoordYOffset || 0;
        const cx = this.naturalWidth / 2, cy = this.naturalHeight / 2 + yOff;
        const g = this.createSVGElement('g', {class: 'scroll-marker'});
        g.appendChild(this.createSVGElement('circle', {cx, cy, r:50, fill:'rgba(59,130,246,0.2)', stroke:color, 'stroke-width':3}));
        const arrowPath = isUp
            ? `M ${cx} ${cy-30} L ${cx-20} ${cy} L ${cx-8} ${cy} L ${cx-8} ${cy+25} L ${cx+8} ${cy+25} L ${cx+8} ${cy} L ${cx+20} ${cy} Z`
            : `M ${cx} ${cy+30} L ${cx-20} ${cy} L ${cx-8} ${cy} L ${cx-8} ${cy-25} L ${cx+8} ${cy-25} L ${cx+8} ${cy} L ${cx+20} ${cy} Z`;
        g.appendChild(this.createSVGElement('path', {d:arrowPath, fill:color, opacity:0.9}));
        const label = this.createSVGElement('text', {x:cx, y:cy+70, fill:color, 'font-size':16, 'font-weight':'bold', 'font-family':'Arial, sans-serif', 'text-anchor':'middle'});
        label.textContent = `scroll ${isUp ? '↑ UP' : '↓ DOWN'} ${Math.abs(pixels)}px`;
        g.appendChild(label);
        this.overlay.appendChild(g);
        this._nonCoordYOffset = yOff + 160;
    }
    
    drawTypeIndicator(text) {
        if (!text) return;
        const color = this.colors.type;
        const yOff = this._nonCoordYOffset || 0;
        const g = this.createSVGElement('g', {class: 'type-marker'});
        const bw = Math.min(this.naturalWidth - 40, 500);
        const bx = (this.naturalWidth - bw) / 2;
        const by = 20 + yOff;
        g.appendChild(this.createSVGElement('rect', {x:bx, y:by, width:bw, height:60, rx:8, fill:color, opacity:0.95}));
        const icon = this.createSVGElement('text', {x:bx+15, y:by+38, fill:'white', 'font-size':28, 'font-family':'Arial, sans-serif'});
        icon.textContent = '⌨';
        g.appendChild(icon);
        const display = text.length > 50 ? text.substring(0, 47) + '...' : text;
        const tl = this.createSVGElement('text', {x:bx+50, y:by+35, fill:'white', 'font-size':16, 'font-family':'Monaco, monospace'});
        tl.textContent = `"${display}"`;
        g.appendChild(tl);
        this.overlay.appendChild(g);
        this._nonCoordYOffset = yOff + 80;
    }
    
    drawHotkeyIndicator(keys, actionType) {
        if (!keys || keys.length === 0) return;
        const color = this.colors.hotkey;
        const yOff = this._nonCoordYOffset || 0;
        const g = this.createSVGElement('g', {class: 'hotkey-marker'});
        const keysText = keys.join(' + ');
        const bw = Math.min(this.naturalWidth - 40, 400);
        const bx = (this.naturalWidth - bw) / 2;
        const by = 20 + yOff;
        g.appendChild(this.createSVGElement('rect', {x:bx, y:by, width:bw, height:60, rx:8, fill:color, opacity:0.95}));
        const tl = this.createSVGElement('text', {x:bx+15, y:by+25, fill:'white', 'font-size':12, 'font-family':'Arial, sans-serif'});
        tl.textContent = actionType.toUpperCase();
        g.appendChild(tl);
        const kl = this.createSVGElement('text', {x:bx+15, y:by+48, fill:'white', 'font-size':20, 'font-weight':'bold', 'font-family':'Monaco, monospace'});
        kl.textContent = keysText;
        g.appendChild(kl);
        this.overlay.appendChild(g);
        this._nonCoordYOffset = yOff + 80;
    }
    
    drawWaitIndicator(time) {
        const color = this.colors.wait;
        const yOff = this._nonCoordYOffset || 0;
        const cx = this.naturalWidth / 2, cy = this.naturalHeight / 2 + yOff;
        const g = this.createSVGElement('g', {class: 'wait-marker'});
        g.appendChild(this.createSVGElement('circle', {cx, cy, r:40, fill:'rgba(100,116,139,0.3)', stroke:color, 'stroke-width':4}));
        g.appendChild(this.createSVGElement('line', {x1:cx, y1:cy, x2:cx, y2:cy-20, stroke:color, 'stroke-width':4, 'stroke-linecap':'round'}));
        g.appendChild(this.createSVGElement('line', {x1:cx, y1:cy, x2:cx+15, y2:cy-10, stroke:color, 'stroke-width':3, 'stroke-linecap':'round'}));
        const label = this.createSVGElement('text', {x:cx, y:cy+65, fill:color, 'font-size':18, 'font-weight':'bold', 'font-family':'Arial, sans-serif', 'text-anchor':'middle'});
        label.textContent = `wait ${time}s`;
        g.appendChild(label);
        this.overlay.appendChild(g);
        this._nonCoordYOffset = yOff + 140;
    }
    
    drawFinishedIndicator(status) {
        const isSuccess = status === 'success';
        const color = isSuccess ? '#22c55e' : '#ef4444';
        const cx = this.naturalWidth / 2, cy = this.naturalHeight / 2;
        const g = this.createSVGElement('g', {class: 'finished-marker'});
        g.appendChild(this.createSVGElement('circle', {cx, cy, r:60, fill:`rgba(${isSuccess ? '34,197,94' : '239,68,68'},0.2)`, stroke:color, 'stroke-width':5}));
        if (isSuccess) {
            g.appendChild(this.createSVGElement('path', {d:`M ${cx-25} ${cy} L ${cx-5} ${cy+20} L ${cx+30} ${cy-25}`, fill:'none', stroke:color, 'stroke-width':8, 'stroke-linecap':'round', 'stroke-linejoin':'round'}));
        } else {
            g.appendChild(this.createSVGElement('line', {x1:cx-25, y1:cy-25, x2:cx+25, y2:cy+25, stroke:color, 'stroke-width':8, 'stroke-linecap':'round'}));
            g.appendChild(this.createSVGElement('line', {x1:cx+25, y1:cy-25, x2:cx-25, y2:cy+25, stroke:color, 'stroke-width':8, 'stroke-linecap':'round'}));
        }
        const label = this.createSVGElement('text', {x:cx, y:cy+90, fill:color, 'font-size':24, 'font-weight':'bold', 'font-family':'Arial, sans-serif', 'text-anchor':'middle'});
        label.textContent = isSuccess ? 'FINISHED - SUCCESS' : 'FINISHED - FAILURE';
        g.appendChild(label);
        this.overlay.appendChild(g);
    }
    
    getTextWidth(text) {
        return text.length * 8 + 10;
    }
}
