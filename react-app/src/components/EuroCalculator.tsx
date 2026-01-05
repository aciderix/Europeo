/**
 * Euro Calculator - Faithful port of euro32 calculette.dll
 * A currency converter calculator with 2002 exchange rates
 *
 * Original DFM Layout (178x291):
 * - EC_Montant_Mon (display): (4, 12) 169x25 - blue text on white
 * - Im_Monnaie1 (source flag): (8, 48) 25x21
 * - L_monnaie1 (source code): (30, 50) "FRF"
 * - Im_monnaie2 (target flag): (148, 48) 25x21
 * - L_monnaie2 (target code): (88, 50) "EUR"
 * - b_move (swap): (132, 80) 32x32
 * - b_quitter (quit): (6, 76) 50x52
 * - ECClavier1 (keypad): (8, 132) 161x153
 */

import React, { useState, useCallback } from 'react';

interface EuroCalculatorProps {
  onClose: () => void;
}

// Currency definitions with images and exchange rates (1 EUR = X currency)
// Official irrevocable rates fixed by EU
const CURRENCIES: {
  code: string;
  name: string;
  image: string;
  rate: number; // Rate to EUR (1 EUR = rate units of this currency)
}[] = [
  { code: 'EUR', name: 'Euro', image: '/assets/calculator/Image_13.png', rate: 1 },
  { code: 'FRF', name: 'Franc Français', image: '/assets/calculator/Image_18.png', rate: 6.55957 },
  { code: 'DEM', name: 'Deutsche Mark', image: '/assets/calculator/Image_19.png', rate: 1.95583 },
  { code: 'BEF', name: 'Franc Belge', image: '/assets/calculator/Image_8.png', rate: 40.3399 },
  { code: 'LUF', name: 'Franc Luxembourgeois', image: '/assets/calculator/Image_15.png', rate: 40.3399 },
  { code: 'ESP', name: 'Peseta Espagnole', image: '/assets/calculator/Image_5.png', rate: 166.386 },
  { code: 'ITL', name: 'Lire Italienne', image: '/assets/calculator/Image_21.png', rate: 1936.27 },
  { code: 'NLG', name: 'Florin Néerlandais', image: '/assets/calculator/Image_11.png', rate: 2.20371 },
  { code: 'ATS', name: 'Schilling Autrichien', image: '/assets/calculator/Image_9.png', rate: 13.7603 },
  { code: 'PTE', name: 'Escudo Portugais', image: '/assets/calculator/Image_4.png', rate: 200.482 },
  { code: 'FIM', name: 'Mark Finlandais', image: '/assets/calculator/Image_7.png', rate: 5.94573 },
  { code: 'IEP', name: 'Livre Irlandaise', image: '/assets/calculator/Image_16.png', rate: 0.787564 },
  { code: 'GRD', name: 'Drachme Grecque', image: '/assets/calculator/Image_3.png', rate: 340.750 },
  { code: 'USD', name: 'Dollar US', image: '/assets/calculator/Image_2.png', rate: 0.90 }, // ~2002 rate
  { code: 'GBP', name: 'Livre Sterling', image: '/assets/calculator/Image_12.png', rate: 0.63 },
  { code: 'CHF', name: 'Franc Suisse', image: '/assets/calculator/Image_22.png', rate: 1.45 },
  { code: 'JPY', name: 'Yen Japonais', image: '/assets/calculator/Image_6.png', rate: 118 },
  { code: 'SEK', name: 'Couronne Suédoise', image: '/assets/calculator/Image_10.png', rate: 9.16 },
  { code: 'DKK', name: 'Couronne Danoise', image: '/assets/calculator/Image_20.png', rate: 7.43 },
  { code: 'NOK', name: 'Couronne Norvégienne', image: '/assets/calculator/Image_14.png', rate: 7.51 },
  { code: 'CAD', name: 'Dollar Canadien', image: '/assets/calculator/Image_17.png', rate: 1.41 },
];

// Asset paths
const SWAP_BUTTON = '/assets/calculator/Image_28.png';
const SWAP_BUTTON_HOVER = '/assets/calculator/Image_27.png';
const SWAP_BUTTON_DOWN = '/assets/calculator/Image_29.png';
const QUIT_BUTTON = '/assets/calculator/Image_31.png';
const QUIT_BUTTON_HOVER = '/assets/calculator/Image_30.png';

export const EuroCalculator: React.FC<EuroCalculatorProps> = ({ onClose }) => {
  const [display, setDisplay] = useState('0');
  const [sourceCurrency, setSourceCurrency] = useState(CURRENCIES.find(c => c.code === 'FRF')!);
  const [targetCurrency, setTargetCurrency] = useState(CURRENCIES.find(c => c.code === 'EUR')!);
  const [operator, setOperator] = useState<string | null>(null);
  const [previousValue, setPreviousValue] = useState<number | null>(null);
  const [waitingForOperand, setWaitingForOperand] = useState(false);
  const [showSourceDropdown, setShowSourceDropdown] = useState(false);
  const [showTargetDropdown, setShowTargetDropdown] = useState(false);
  const [swapHover, setSwapHover] = useState(false);
  const [swapDown, setSwapDown] = useState(false);
  const [quitHover, setQuitHover] = useState(false);

  // Convert value from source to target currency
  const convertValue = useCallback((value: number, from: typeof CURRENCIES[0], to: typeof CURRENCIES[0]): number => {
    // Convert to EUR first, then to target
    const inEur = value / from.rate;
    return inEur * to.rate;
  }, []);

  // Format display value
  const formatDisplay = useCallback((value: string, currency: typeof CURRENCIES[0]): string => {
    const num = parseFloat(value);
    if (isNaN(num)) return `0 ${currency.code}`;

    // Format based on currency (more decimals for small rates like IEP)
    let formatted: string;
    if (currency.rate < 1) {
      formatted = num.toFixed(4);
    } else if (currency.rate > 100) {
      formatted = num.toFixed(0);
    } else {
      formatted = num.toFixed(2);
    }

    return `${formatted} ${currency.code}`;
  }, []);

  // Handle digit input
  const handleDigit = useCallback((digit: string) => {
    if (waitingForOperand) {
      setDisplay(digit);
      setWaitingForOperand(false);
    } else {
      setDisplay(display === '0' ? digit : display + digit);
    }
  }, [display, waitingForOperand]);

  // Handle decimal point
  const handleDecimal = useCallback(() => {
    if (waitingForOperand) {
      setDisplay('0.');
      setWaitingForOperand(false);
    } else if (!display.includes('.')) {
      setDisplay(display + '.');
    }
  }, [display, waitingForOperand]);

  // Handle operator
  const handleOperator = useCallback((op: string) => {
    const value = parseFloat(display);

    if (previousValue !== null && operator && !waitingForOperand) {
      let result: number;
      switch (operator) {
        case '+': result = previousValue + value; break;
        case '-': result = previousValue - value; break;
        case '*': result = previousValue * value; break;
        case '/': result = value !== 0 ? previousValue / value : 0; break;
        default: result = value;
      }
      setDisplay(String(result));
      setPreviousValue(result);
    } else {
      setPreviousValue(value);
    }

    setOperator(op);
    setWaitingForOperand(true);
  }, [display, operator, previousValue, waitingForOperand]);

  // Handle equals
  const handleEquals = useCallback(() => {
    const value = parseFloat(display);

    if (previousValue !== null && operator) {
      let result: number;
      switch (operator) {
        case '+': result = previousValue + value; break;
        case '-': result = previousValue - value; break;
        case '*': result = previousValue * value; break;
        case '/': result = value !== 0 ? previousValue / value : 0; break;
        default: result = value;
      }
      setDisplay(String(result));
      setPreviousValue(null);
      setOperator(null);
      setWaitingForOperand(true);
    }
  }, [display, operator, previousValue]);

  // Clear
  const handleClear = useCallback(() => {
    setDisplay('0');
    setPreviousValue(null);
    setOperator(null);
    setWaitingForOperand(false);
  }, []);

  // Clear entry
  const handleClearEntry = useCallback(() => {
    setDisplay('0');
    setWaitingForOperand(false);
  }, []);

  // Swap currencies
  const handleSwap = useCallback(() => {
    const currentValue = parseFloat(display);
    const convertedValue = convertValue(currentValue, sourceCurrency, targetCurrency);

    const temp = sourceCurrency;
    setSourceCurrency(targetCurrency);
    setTargetCurrency(temp);
    setDisplay(String(convertedValue));
  }, [display, sourceCurrency, targetCurrency, convertValue]);

  // Get converted display value
  const getConvertedValue = (): string => {
    const value = parseFloat(display);
    if (isNaN(value)) return formatDisplay('0', targetCurrency);
    const converted = convertValue(value, sourceCurrency, targetCurrency);
    return formatDisplay(String(converted), targetCurrency);
  };

  // Keypad button style
  const keyStyle: React.CSSProperties = {
    width: 27,
    height: 27,
    margin: 1,
    border: '1px solid #888',
    borderRadius: 3,
    backgroundColor: '#e0e0e0',
    cursor: 'pointer',
    fontFamily: 'MS Sans Serif, Arial, sans-serif',
    fontSize: 12,
    fontWeight: 'bold',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  };

  const operatorKeyStyle: React.CSSProperties = {
    ...keyStyle,
    backgroundColor: '#c0c0ff',
  };

  const clearKeyStyle: React.CSSProperties = {
    ...keyStyle,
    backgroundColor: '#ffc0c0',
  };

  return (
    <div style={{
      position: 'fixed',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      zIndex: 2000,
    }}>
      {/* Main calculator panel - exact DFM size 178x291 */}
      <div style={{
        position: 'relative',
        width: 178,
        height: 291,
        backgroundColor: '#FFC0FF', // Color 16732415 from DFM (pink/magenta tint)
        border: '2px outset #d0d0d0',
        fontFamily: 'MS Sans Serif, Arial, sans-serif',
      }}>
        {/* Display - EC_Montant_Mon at (4, 12) 169x25 */}
        <div style={{
          position: 'absolute',
          left: 4,
          top: 12,
          width: 169,
          height: 25,
          backgroundColor: '#fff',
          border: '2px inset #808080',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'flex-end',
          paddingRight: 4,
          fontSize: 15,
          fontFamily: 'MS Sans Serif, Arial, sans-serif',
          color: '#0000FF',
          overflow: 'hidden',
        }}>
          {formatDisplay(display, sourceCurrency)}
        </div>

        {/* Source currency selector */}
        <div style={{ position: 'absolute', left: 8, top: 44 }}>
          {/* Flag */}
          <img
            src={sourceCurrency.image}
            alt={sourceCurrency.code}
            onClick={() => { setShowSourceDropdown(!showSourceDropdown); setShowTargetDropdown(false); }}
            style={{
              position: 'absolute',
              left: 0,
              top: 4,
              width: 25,
              height: 21,
              cursor: 'pointer',
              border: '1px solid #888',
            }}
          />
          {/* Code label */}
          <span
            onClick={() => { setShowSourceDropdown(!showSourceDropdown); setShowTargetDropdown(false); }}
            style={{
              position: 'absolute',
              left: 30,
              top: 6,
              width: 40,
              fontSize: 11,
              fontWeight: 'bold',
              color: '#808080',
              cursor: 'pointer',
            }}
          >
            {sourceCurrency.code}
          </span>

          {/* Dropdown */}
          {showSourceDropdown && (
            <div style={{
              position: 'absolute',
              left: 0,
              top: 28,
              width: 150,
              maxHeight: 200,
              overflowY: 'auto',
              backgroundColor: '#fff',
              border: '1px solid #000',
              zIndex: 100,
            }}>
              {CURRENCIES.map(c => (
                <div
                  key={c.code}
                  onClick={() => { setSourceCurrency(c); setShowSourceDropdown(false); }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    padding: '2px 4px',
                    cursor: 'pointer',
                    backgroundColor: c.code === sourceCurrency.code ? '#0000FF' : '#fff',
                    color: c.code === sourceCurrency.code ? '#fff' : '#000',
                  }}
                >
                  <img src={c.image} alt="" style={{ width: 20, height: 16, marginRight: 4 }} />
                  <span style={{ fontSize: 10 }}>{c.code} - {c.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Target currency selector */}
        <div style={{ position: 'absolute', left: 88, top: 44 }}>
          {/* Code label */}
          <span
            onClick={() => { setShowTargetDropdown(!showTargetDropdown); setShowSourceDropdown(false); }}
            style={{
              position: 'absolute',
              left: 0,
              top: 6,
              width: 40,
              fontSize: 11,
              fontWeight: 'bold',
              color: '#808080',
              cursor: 'pointer',
              textAlign: 'center',
            }}
          >
            {targetCurrency.code}
          </span>
          {/* Flag */}
          <img
            src={targetCurrency.image}
            alt={targetCurrency.code}
            onClick={() => { setShowTargetDropdown(!showTargetDropdown); setShowSourceDropdown(false); }}
            style={{
              position: 'absolute',
              left: 60,
              top: 4,
              width: 25,
              height: 21,
              cursor: 'pointer',
              border: '1px solid #888',
            }}
          />

          {/* Dropdown */}
          {showTargetDropdown && (
            <div style={{
              position: 'absolute',
              left: -60,
              top: 28,
              width: 150,
              maxHeight: 200,
              overflowY: 'auto',
              backgroundColor: '#fff',
              border: '1px solid #000',
              zIndex: 100,
            }}>
              {CURRENCIES.map(c => (
                <div
                  key={c.code}
                  onClick={() => { setTargetCurrency(c); setShowTargetDropdown(false); }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    padding: '2px 4px',
                    cursor: 'pointer',
                    backgroundColor: c.code === targetCurrency.code ? '#0000FF' : '#fff',
                    color: c.code === targetCurrency.code ? '#fff' : '#000',
                  }}
                >
                  <img src={c.image} alt="" style={{ width: 20, height: 16, marginRight: 4 }} />
                  <span style={{ fontSize: 10 }}>{c.code} - {c.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quit button - b_quitter at (6, 76) 50x52 */}
        <img
          src={quitHover ? QUIT_BUTTON_HOVER : QUIT_BUTTON}
          alt="Quitter"
          onClick={onClose}
          onMouseEnter={() => setQuitHover(true)}
          onMouseLeave={() => setQuitHover(false)}
          style={{
            position: 'absolute',
            left: 6,
            top: 76,
            width: 50,
            height: 52,
            cursor: 'pointer',
          }}
        />

        {/* Converted value display */}
        <div style={{
          position: 'absolute',
          left: 60,
          top: 82,
          width: 70,
          fontSize: 11,
          color: '#0000FF',
          fontWeight: 'bold',
          textAlign: 'right',
        }}>
          {getConvertedValue()}
        </div>

        {/* Swap button - b_move at (132, 80) 32x32 */}
        <img
          src={swapDown ? SWAP_BUTTON_DOWN : (swapHover ? SWAP_BUTTON_HOVER : SWAP_BUTTON)}
          alt="Swap"
          onClick={handleSwap}
          onMouseEnter={() => setSwapHover(true)}
          onMouseLeave={() => { setSwapHover(false); setSwapDown(false); }}
          onMouseDown={() => setSwapDown(true)}
          onMouseUp={() => setSwapDown(false)}
          style={{
            position: 'absolute',
            left: 132,
            top: 80,
            width: 32,
            height: 32,
            cursor: 'pointer',
          }}
        />

        {/* Keypad - ECClavier1 at (8, 132) 161x153 */}
        <div style={{
          position: 'absolute',
          left: 8,
          top: 132,
          width: 161,
          height: 153,
        }}>
          {/* Row 1: 7 8 9 / C */}
          <div style={{ display: 'flex' }}>
            <div style={keyStyle} onClick={() => handleDigit('7')}>7</div>
            <div style={keyStyle} onClick={() => handleDigit('8')}>8</div>
            <div style={keyStyle} onClick={() => handleDigit('9')}>9</div>
            <div style={operatorKeyStyle} onClick={() => handleOperator('/')}>/</div>
            <div style={clearKeyStyle} onClick={handleClear}>C</div>
          </div>
          {/* Row 2: 4 5 6 * CE */}
          <div style={{ display: 'flex' }}>
            <div style={keyStyle} onClick={() => handleDigit('4')}>4</div>
            <div style={keyStyle} onClick={() => handleDigit('5')}>5</div>
            <div style={keyStyle} onClick={() => handleDigit('6')}>6</div>
            <div style={operatorKeyStyle} onClick={() => handleOperator('*')}>*</div>
            <div style={clearKeyStyle} onClick={handleClearEntry}>CE</div>
          </div>
          {/* Row 3: 1 2 3 - */}
          <div style={{ display: 'flex' }}>
            <div style={keyStyle} onClick={() => handleDigit('1')}>1</div>
            <div style={keyStyle} onClick={() => handleDigit('2')}>2</div>
            <div style={keyStyle} onClick={() => handleDigit('3')}>3</div>
            <div style={operatorKeyStyle} onClick={() => handleOperator('-')}>-</div>
            <div style={{ ...keyStyle, visibility: 'hidden' }}></div>
          </div>
          {/* Row 4: 0 , = + */}
          <div style={{ display: 'flex' }}>
            <div style={keyStyle} onClick={() => handleDigit('0')}>0</div>
            <div style={keyStyle} onClick={handleDecimal}>,</div>
            <div style={{ ...operatorKeyStyle, backgroundColor: '#90EE90' }} onClick={handleEquals}>=</div>
            <div style={operatorKeyStyle} onClick={() => handleOperator('+')}>+</div>
            <div style={{ ...keyStyle, visibility: 'hidden' }}></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EuroCalculator;
