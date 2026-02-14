import React, { useState, useMemo, useRef, useEffect } from 'react';
import type { DeckCard } from '../../types/deck';
import { PlusIcon, MinusIcon, TrashIcon, SparklesIcon, Squares2X2Icon, ListBulletIcon, ChevronDownIcon, ChevronRightIcon, XMarkIcon } from '@heroicons/react/24/outline';
import ManaCost from '../common/ManaCost';
import PowerToughness from '../common/PowerToughness';

interface CardListProps {
  cards: DeckCard[];
  onUpdateQuantity: (cardId: number, newQuantity: number) => void;
  onRemoveCard: (cardId: number) => void;
  commander?: DeckCard;
}

type ViewMode = 'grid' | 'list';
type GroupBy = 'type' | 'none' | 'cmc' | 'color' | 'rarity' | 'set';

const TRIGGER_LABELS = ['ETB', 'Dies', 'Attacks', 'Tap', 'Upkeep', 'EOT', 'Cast', 'Create', 'Sacrifice', 'Destroy'];

const CardList: React.FC<CardListProps> = ({ cards, onUpdateQuantity, onRemoveCard, commander }) => {
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [groupBy, setGroupBy] = useState<GroupBy>('type');
  const [hoveredCard, setHoveredCard] = useState<DeckCard | null>(null);
  const [hoveredCardFaceIndex, setHoveredCardFaceIndex] = useState<Record<number, number>>({});
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set());
  const [keywordFilter, setKeywordFilter] = useState<string[]>([]);
  const [triggerFilter, setTriggerFilter] = useState<string[]>([]);
  const [keywordDropdownOpen, setKeywordDropdownOpen] = useState(false);
  const [triggerDropdownOpen, setTriggerDropdownOpen] = useState(false);
  const [keywordSearch, setKeywordSearch] = useState('');
  const [triggerSearch, setTriggerSearch] = useState('');
  const [keywordMatchMode, setKeywordMatchMode] = useState<'OR' | 'AND'>('OR');
  const [triggerMatchMode, setTriggerMatchMode] = useState<'OR' | 'AND'>('OR');
  const keywordDropdownRef = useRef<HTMLDivElement>(null);
  const triggerDropdownRef = useRef<HTMLDivElement>(null);

  const allKeywords = useMemo(() => {
    const keywords = new Set<string>();
    cards.forEach(card => {
      card.keywords?.forEach(k => keywords.add(k));
    });
    return Array.from(keywords).sort();
  }, [cards]);

  const getCardAbilities = (oracleText?: string): string[] => {
    if (!oracleText) return [];
    
    const triggers: [RegExp, string][] = [
      [/enters the battlefield/i, 'ETB'],
      [/dies/i, 'Dies'],
      [/when.* attacks/i, 'Attacks'],
      [/when.* becomes tapped/i, 'Tap'],
      [/at the beginning of your upkeep/i, 'Upkeep'],
      [/at the beginning of each end step/i, 'EOT'],
      [/when you cast/i, 'Cast'],
      [/whenever you.*create/i, 'Create'],
      [/whenever a creature.*enters/i, 'ETB'],
      [/whenever a creature.*dies/i, 'Dies'],
      [/sacrifice/i, 'Sacrifice'],
      [/destroy/i, 'Destroy'],
      [/{T},? pay/i, 'Activated'],
      [/discard/i, 'Discard'],
      [/draw a card|draw cards|draw card/i, 'Draw'],
      [/lose (\d+ )?life|lose life/i, 'Lose Life'],
      [/gain (\d+ )?life|gain life/i, 'Gain Life'],
      [/put (\d+ )?counter|place (\d+ )?counter| counters/i, 'Counters'],
      [/deals? \d+ damage|deal \d+ damage|damage/i, 'Deal Damage'],
    ];
    
    const found: string[] = [];
    for (const [regex, label] of triggers) {
      if (regex.test(oracleText)) {
        if (!found.includes(label)) {
          found.push(label);
        }
      }
    }
    return found;
  };

  const availableTriggers = useMemo(() => {
    const triggers = new Set<string>();
    cards.forEach(card => {
      const found = getCardAbilities(card.oracle_text);
      found.forEach(t => triggers.add(t));
    });
    return Array.from(triggers).sort();
  }, [cards]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (keywordDropdownRef.current && !keywordDropdownRef.current.contains(event.target as Node)) {
        setKeywordDropdownOpen(false);
      }
      if (triggerDropdownRef.current && !triggerDropdownRef.current.contains(event.target as Node)) {
        setTriggerDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getGroupLabel = (group: string): string => {
    switch (groupBy) {
      case 'cmc':
        const cmc = parseInt(group);
        return cmc === 0 ? 'Land (0)' : cmc === 1 ? '1' : cmc === 2 ? '2' : cmc === 3 ? '3' : cmc === 4 ? '4' : cmc === 5 ? '5' : cmc === 6 ? '6' : cmc >= 7 ? '7+' : group;
      case 'color':
        if (group === 'C') return 'Colorless';
        if (group === 'W') return 'White';
        if (group === 'U') return 'Blue';
        if (group === 'B') return 'Black';
        if (group === 'R') return 'Red';
        if (group === 'G') return 'Green';
        if (group === 'WU') return 'White/Blue';
        if (group === 'UB') return 'Blue/Black';
        if (group === 'BR') return 'Black/Red';
        if (group === 'RG') return 'Red/Green';
        if (group === 'GW') return 'Green/White';
        if (group === 'WU-B') return 'White/Blue/Black';
        if (group === 'WUB') return 'White/Blue/Black';
        if (group === 'UBR') return 'Blue/Black/Red';
        if (group === 'BRG') return 'Black/Red/Green';
        if (group === 'R GW') return 'Red/Green/White';
        if (group === 'GWU') return 'Green/White/Blue';
        return group;
      case 'rarity':
        if (group === 'mythic') return 'Mythic';
        if (group === 'rare') return 'Rare';
        if (group === 'uncommon') return 'Uncommon';
        if (group === 'common') return 'Common';
        return group;
      case 'set':
        return group.toUpperCase();
      default:
        return group;
    }
  };

  const toggleGroup = (group: string) => {
    setCollapsedGroups(prev => {
      const newSet = new Set(prev);
      if (newSet.has(group)) {
        newSet.delete(group);
      } else {
        newSet.add(group);
      }
      return newSet;
    });
  };

  const expandAll = () => setCollapsedGroups(new Set());

  const totalCards = useMemo(() => {
    return cards.reduce((sum, card) => sum + card.quantity, 0);
  }, [cards]);

  const sortedCards = useMemo(() => {
    let result = [...cards];
    
    if (keywordFilter.length > 0) {
      if (keywordMatchMode === 'OR') {
        result = result.filter(card => 
          card.keywords?.some(k => keywordFilter.includes(k))
        );
      } else {
        result = result.filter(card => 
          card.keywords && keywordFilter.every(kw => card.keywords?.includes(kw))
        );
      }
    }
    
    if (triggerFilter.length > 0) {
      if (triggerMatchMode === 'OR') {
        result = result.filter(card => 
          getCardAbilities(card.oracle_text).some(t => triggerFilter.includes(t))
        );
      } else {
        result = result.filter(card => {
          const cardTriggers = getCardAbilities(card.oracle_text);
          return cardTriggers.length > 0 && triggerFilter.every(trig => cardTriggers.includes(trig));
        });
      }
    }
    
    return result.sort((a, b) => {
      if (a.is_commander && !b.is_commander) return -1;
      if (!a.is_commander && b.is_commander) return 1;
      
      const typeA = a.type_line || '';
      const typeB = b.type_line || '';
      
      const isCreatureA = typeA.toLowerCase().includes('creature');
      const isCreatureB = typeB.toLowerCase().includes('creature');
      
      if (isCreatureA && !isCreatureB) return -1;
      if (!isCreatureA && isCreatureB) return 1;
      
      return (a.card_name || '').localeCompare(b.card_name || '');
    });
  }, [cards, keywordFilter, triggerFilter, keywordMatchMode, triggerMatchMode]);

  const groupedCards = useMemo(() => {
    if (groupBy === 'none') {
      return { 'All Cards': sortedCards };
    }
    
    if (groupBy === 'cmc') {
      return sortedCards.reduce((groups, card) => {
        let group = 'Other';
        if (card.is_commander) {
          group = 'Commander';
        } else if (card.cmc !== undefined) {
          if (card.cmc === 0) group = '0';
          else if (card.cmc >= 7) group = '7+';
          else group = Math.floor(card.cmc).toString();
        }
        if (!groups[group]) groups[group] = [];
        groups[group].push(card);
        return groups;
      }, {} as Record<string, DeckCard[]>);
    }
    
    if (groupBy === 'color') {
      return sortedCards.reduce((groups, card) => {
        let group = 'C';
        if (card.is_commander) {
          group = 'Commander';
        } else if (card.colors && card.colors.length > 0) {
          group = card.colors.sort().join('');
        }
        if (!groups[group]) groups[group] = [];
        groups[group].push(card);
        return groups;
      }, {} as Record<string, DeckCard[]>);
    }
    
    if (groupBy === 'rarity') {
      return sortedCards.reduce((groups, card) => {
        let group = 'common';
        if (card.is_commander) {
          group = 'Commander';
        } else if (card.rarity) {
          group = card.rarity;
        }
        if (!groups[group]) groups[group] = [];
        groups[group].push(card);
        return groups;
      }, {} as Record<string, DeckCard[]>);
    }
    
    if (groupBy === 'set') {
      return sortedCards.reduce((groups, card) => {
        let group = 'Other';
        if (card.is_commander) {
          group = 'Commander';
        } else if (card.set) {
          group = card.set;
        }
        if (!groups[group]) groups[group] = [];
        groups[group].push(card);
        return groups;
      }, {} as Record<string, DeckCard[]>);
    }
    
    // Default: group by type
    return sortedCards.reduce((groups, card) => {
      let type = 'Other';
      const typeLine = card.type_line || '';
      
      if (card.is_commander) {
        type = 'Commander';
      } else if (typeLine.includes('Creature')) {
        type = 'Creatures';
      } else if (typeLine.includes('Instant')) {
        type = 'Instants';
      } else if (typeLine.includes('Sorcery')) {
        type = 'Sorceries';
      } else if (typeLine.includes('Artifact')) {
        type = 'Artifacts';
      } else if (typeLine.includes('Enchantment')) {
        type = 'Enchantments';
      } else if (typeLine.includes('Planeswalker')) {
        type = 'Planeswalkers';
      } else if (typeLine.includes('Land')) {
        type = 'Lands';
      }
      
      if (!groups[type]) {
        groups[type] = [];
      }
      groups[type].push(card);
      return groups;
    }, {} as Record<string, DeckCard[]>);
  }, [sortedCards, groupBy]);

  const baseGroupOrder = groupBy === 'cmc' 
    ? ['Commander', '0', '1', '2', '3', '4', '5', '6', '7+', 'Other']
    : groupBy === 'color'
    ? ['Commander', 'W', 'U', 'B', 'R', 'G', 'WU', 'UB', 'BR', 'RG', 'GW', 'WUB', 'UBR', 'BRG', 'RGW', 'GWU', 'C']
    : groupBy === 'rarity'
    ? ['Commander', 'mythic', 'rare', 'uncommon', 'common']
    : groupBy === 'set'
    ? []
    : ['Commander', 'Creatures', 'Planeswalkers', 'Artifacts', 'Enchantments', 'Instants', 'Sorceries', 'Lands', 'Other', 'All Cards'];

  // Calculate effectiveGroupOrder after groupedCards is defined
  const effectiveGroupOrder = groupBy === 'set' 
    ? Object.keys(groupedCards).sort()
    : baseGroupOrder;

  const hasAnyCollapsed = Object.keys(groupedCards).some(g => collapsedGroups.has(g));

  const handleCollapseAll = () => {
    const allGroups = Object.keys(groupedCards).filter(g => groupedCards[g]?.length > 0);
    setCollapsedGroups(new Set(allGroups));
  };

  const getCardFaceImage = (card: DeckCard, faceIndex: number) => {
    if (card.card_faces && card.card_faces.length > 0 && card.card_faces[faceIndex]?.image_uris) {
      return card.card_faces[faceIndex].image_uris;
    }
    return card.image_uris;
  };

  const hasMultipleFaces = (card: DeckCard) => {
    return card.card_faces && card.card_faces.length > 1;
  };

  const displayCard = hoveredCard || (commander ? {
    card_name: commander.card_name,
    image_uris: commander.image_uris,
    mana_cost: commander.mana_cost,
    type_line: commander.type_line,
    card_faces: commander.card_faces,
    power: commander.power,
    toughness: commander.toughness
  } : null);

  const displayFaceIndex = displayCard ? hoveredCardFaceIndex[displayCard.id] || 0 : 0;
  const displayPower = displayCard?.card_faces?.[displayFaceIndex]?.power || displayCard?.power;
  const displayToughness = displayCard?.card_faces?.[displayFaceIndex]?.toughness || displayCard?.toughness;

  const renderCard = (card: DeckCard, isCompact = false) => {
    const faceIndex = hoveredCardFaceIndex[card.id] || 0;
    const cardImage = card.card_faces?.[faceIndex]?.image_uris?.small || card.image_uris?.small;
    const faceManaCost = card.card_faces?.[faceIndex]?.mana_cost || card.mana_cost;
    const facePower = card.card_faces?.[faceIndex]?.power || card.power;
    const faceToughness = card.card_faces?.[faceIndex]?.toughness || card.toughness;
    const faceOracleText = card.card_faces?.[faceIndex]?.oracle_text || card.oracle_text;
    
    return (
    <div
      key={card.id}
      className={`flex items-center justify-between px-4 py-3 hover:bg-gray-700/30 transition-colors ${
        card.is_commander ? 'bg-yellow-500/5' : ''
      }`}
      onMouseEnter={() => setHoveredCard(card)}
      onMouseLeave={() => setHoveredCard(null)}
    >
      <div className="flex items-center space-x-3">
        {cardImage ? (
          <img
            src={cardImage}
            alt={card.card_name}
            className={`${isCompact ? 'w-10 h-14' : 'w-12 h-16'} object-cover rounded shadow-md`}
          />
        ) : (
          <div className={`${isCompact ? 'w-10 h-14' : 'w-12 h-16'} bg-gray-700 rounded flex items-center justify-center`}>
            <span className="text-gray-500 text-xs">?</span>
          </div>
        )}
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 flex-wrap">
            <span className="font-medium text-gray-200 truncate">{card.card_name}</span>
            {card.is_commander && (
              <span className="text-yellow-500" title="Commander">
                <SparklesIcon className="h-4 w-4" />
              </span>
            )}
            {card.card_faces && card.card_faces.length > 1 && (
              <button
                type="button"
                onClick={() => {
                  setHoveredCardFaceIndex(prev => ({
                    ...prev,
                    [card.id]: prev[card.id] === 0 ? 1 : 0
                  }));
                }}
                className="p-1 hover:bg-gray-600 rounded"
                title={`Switch to ${faceIndex === 0 ? card.card_faces?.[1]?.name : card.card_faces?.[0]?.name}`}
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 text-gray-400 hover:text-gray-200">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
                </svg>
              </button>
            )}
            {getCardAbilities(faceOracleText).map((trigger) => (
              <span key={trigger} className="px-1.5 py-0.5 bg-purple-600/30 text-purple-300 text-xs rounded">
                {trigger}
              </span>
            ))}
            {card.keywords?.slice(0, 3).map((keyword) => (
              <span key={keyword} className="px-1.5 py-0.5 bg-cyan-600/30 text-cyan-300 text-xs rounded" title={card.keywords?.join(', ')}>
                {keyword}
              </span>
            ))}
          </div>
          <div className="flex items-center gap-3 mt-0.5">
            <ManaCost cost={faceManaCost} showLabel />
            <PowerToughness power={facePower} toughness={faceToughness} showLabel />
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-3">
        {!card.is_commander && (
          <>
            <div className="flex items-center space-x-1">
              <button
                onClick={() => onUpdateQuantity(card.id, card.quantity - 1)}
                disabled={card.quantity <= 1}
                className="p-1 rounded hover:bg-gray-700 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <MinusIcon className="h-4 w-4" />
              </button>
              
              <span className="w-8 text-center font-semibold text-gray-200">
                {card.quantity}
              </span>
              
              <button
                onClick={() => onUpdateQuantity(card.id, card.quantity + 1)}
                disabled={card.quantity >= 99}
                className="p-1 rounded hover:bg-gray-700 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <PlusIcon className="h-4 w-4" />
              </button>
            </div>

            <button
              onClick={() => onRemoveCard(card.id)}
              className="p-1 rounded hover:bg-red-900/30 text-gray-500 hover:text-red-400 transition-colors"
              title="Remove card"
            >
              <TrashIcon className="h-4 w-4" />
            </button>
          </>
        )}
        
        {card.is_commander && (
          <span className="text-yellow-500 text-sm font-medium">Commander</span>
        )}
      </div>
    </div>
  );
  };

  const renderGridCard = (card: DeckCard) => {
    const faceIndex = hoveredCardFaceIndex[card.id] || 0;
    const cardImage = card.card_faces?.[faceIndex]?.image_uris?.normal || card.image_uris?.normal;
    
    return (
    <div
      key={card.id}
      className={`relative group ${card.is_commander ? 'ring-2 ring-yellow-500' : ''}`}
      onMouseEnter={() => setHoveredCard(card)}
      onMouseLeave={() => setHoveredCard(null)}
    >
      {cardImage ? (
        <>
          <img
            src={cardImage}
            alt={card.card_name}
            className="w-full h-auto rounded-lg shadow-md"
          />
          {card.card_faces && card.card_faces.length > 1 && (
            <button
              type="button"
              onClick={(e) => { 
                e.stopPropagation();
                setHoveredCardFaceIndex(prev => ({
                  ...prev,
                  [card.id]: prev[card.id] === 0 ? 1 : 0
                }));
              }}
              className="absolute top-2 left-2 p-1.5 bg-gray-900/80 hover:bg-gray-700 rounded-full shadow-lg transition-colors"
              title={`Show ${faceIndex === 0 ? card.card_faces?.[1]?.name : card.card_faces?.[0]?.name}`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 text-white">
                <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
              </svg>
            </button>
          )}
        </>
      ) : (
        <div className="aspect-[2.5/3.5] bg-gray-700 rounded-lg flex items-center justify-center">
          <span className="text-gray-500">?</span>
        </div>
      )}
      
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent p-2 rounded-b-lg">
        <p className="text-white text-xs font-medium truncate">{card.card_name}</p>
        <ManaCost cost={card.card_faces?.[faceIndex]?.mana_cost || card.mana_cost} className="mt-1" />
      </div>
      
      {!card.is_commander && (
        <div className="absolute top-2 right-2 flex items-center space-x-1 bg-black/60 rounded px-2 py-1">
          <button
            onClick={(e) => { e.stopPropagation(); onUpdateQuantity(card.id, card.quantity - 1); }}
            disabled={card.quantity <= 1}
            className="text-white hover:text-gray-300 disabled:opacity-50"
          >
            <MinusIcon className="h-3 w-3" />
          </button>
          <span className="text-white text-sm font-bold">{card.quantity}</span>
          <button
            onClick={(e) => { e.stopPropagation(); onUpdateQuantity(card.id, card.quantity + 1); }}
            disabled={card.quantity >= 99}
            className="text-white hover:text-gray-300 disabled:opacity-50"
          >
            <PlusIcon className="h-3 w-3" />
          </button>
        </div>
      )}
      
      {card.is_commander && (
        <div className="absolute top-2 left-2 bg-yellow-500 text-black text-xs font-bold px-2 py-1 rounded">
          Commander
        </div>
      )}
    </div>
  );
  };

  return (
    <div className="flex">
      {/* Fixed Card Preview Column - Left Side */}
      <div className="w-1/4 flex-shrink-0 pr-4 hidden lg:block">
        <div className="sticky top-20 z-30">
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl overflow-hidden relative">
            {displayCard && (displayCard.card_faces?.[displayFaceIndex]?.image_uris?.normal || displayCard.image_uris?.normal) ? (
              <>
                <img
                  src={displayCard.card_faces?.[displayFaceIndex]?.image_uris?.normal || displayCard.image_uris?.normal}
                  alt={displayCard.card_name}
                  className="w-full h-auto"
                />
                {displayCard.card_faces && displayCard.card_faces.length > 1 && (
                  <button
                    type="button"
                    onClick={() => setHoveredCardFaceIndex(prev => ({
                      ...prev,
                      [displayCard.id]: prev[displayCard.id] === 0 ? 1 : 0
                    }))}
                    className="absolute bottom-20 right-2 p-2 bg-gray-900/80 hover:bg-gray-700 rounded-full shadow-lg transition-colors"
                    title={`Show ${displayFaceIndex === 0 ? displayCard.card_faces?.[1]?.name : displayCard.card_faces?.[0]?.name}`}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 text-white">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
                    </svg>
                  </button>
                )}
              </>
            ) : (
              <div className="aspect-[2.5/3.5] bg-gray-700 rounded-lg flex items-center justify-center">
                <span className="text-gray-500">No Image</span>
              </div>
            )}
            <div className="p-3 bg-gray-800">
              <p className="text-white font-semibold text-sm">{displayCard?.card_name || 'Hover a card'}</p>
              <div className="flex items-center gap-3 mt-1">
                <ManaCost cost={displayCard?.card_faces?.[displayFaceIndex]?.mana_cost || displayCard?.mana_cost || ''} showLabel />
                {displayPower && displayToughness && (
                  <PowerToughness power={displayPower} toughness={displayToughness} showLabel />
                )}
              </div>
              <p className="text-gray-500 text-xs mt-1 truncate">{displayCard?.card_faces?.[displayFaceIndex]?.type_line || displayCard?.type_line || ''}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content - Right Side */}
      <div className="flex-1 space-y-6">
        {/* Controls Bar */}
        <div className="bg-gray-800/50 rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-gray-400 text-sm">
              Total Cards: <span className="text-white font-semibold">{totalCards}</span>
              {(keywordFilter.length > 0 || triggerFilter.length > 0) && (
                <span className="ml-2 text-yellow-400">
                  (filtered: {sortedCards.length})
                </span>
              )}
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <span className="text-gray-500 text-sm">Group:</span>
                <button
                  type="button"
                  onClick={() => setGroupBy('none')}
                  className={`px-3 py-1 rounded text-sm ${
                    groupBy === 'none' ? 'bg-yellow-500 text-black' : 'bg-gray-700 text-gray-300'
                  }`}
                >
                  None
                </button>
                <button
                  type="button"
                  onClick={() => setGroupBy('type')}
                  className={`px-3 py-1 rounded text-sm ${
                    groupBy === 'type' ? 'bg-yellow-500 text-black' : 'bg-gray-700 text-gray-300'
                  }`}
                >
                  Type
                </button>
                <button
                  type="button"
                  onClick={() => setGroupBy('cmc')}
                  className={`px-3 py-1 rounded text-sm ${
                    groupBy === 'cmc' ? 'bg-yellow-500 text-black' : 'bg-gray-700 text-gray-300'
                  }`}
                >
                  CMC
                </button>
                <button
                  type="button"
                  onClick={() => setGroupBy('color')}
                  className={`px-3 py-1 rounded text-sm ${
                    groupBy === 'color' ? 'bg-yellow-500 text-black' : 'bg-gray-700 text-gray-300'
                  }`}
                >
                  Color
                </button>
                <button
                  type="button"
                  onClick={() => setGroupBy('rarity')}
                  className={`px-3 py-1 rounded text-sm ${
                    groupBy === 'rarity' ? 'bg-yellow-500 text-black' : 'bg-gray-700 text-gray-300'
                  }`}
                >
                  Rarity
                </button>
                <button
                  type="button"
                  onClick={() => setGroupBy('set')}
                  className={`px-3 py-1 rounded text-sm ${
                    groupBy === 'set' ? 'bg-yellow-500 text-black' : 'bg-gray-700 text-gray-300'
                  }`}
                >
                  Set
                </button>
              </div>
              
              <div className="flex items-center space-x-2">
                <span className="text-gray-500 text-sm">View:</span>
                <button
                  type="button"
                  onClick={() => setViewMode('list')}
                  className={`p-2 rounded ${
                    viewMode === 'list' ? 'bg-yellow-500 text-black' : 'bg-gray-700 text-gray-300'
                  }`}
                  title="List view"
                >
                  <ListBulletIcon className="h-5 w-5" />
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode('grid')}
                  className={`p-2 rounded ${
                    viewMode === 'grid' ? 'bg-yellow-500 text-black' : 'bg-gray-700 text-gray-300'
                  }`}
                  title="Grid view"
                >
                  <Squares2X2Icon className="h-5 w-5" />
                </button>
              </div>

              <button
                type="button"
                onClick={() => {
                  if (hasAnyCollapsed) {
                    expandAll();
                  } else {
                    handleCollapseAll();
                  }
                }}
                className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded text-sm"
              >
                {hasAnyCollapsed ? 'Expand All' : 'Collapse All'}
              </button>
            </div>
          </div>
          
          {/* Filters Row */}
          <div className="flex items-center space-x-4 flex-wrap gap-2">
            {/* Keyword Multi-Select */}
            <div className="relative" ref={keywordDropdownRef}>
              <button
                type="button"
                onClick={() => { setKeywordDropdownOpen(!keywordDropdownOpen); setTriggerDropdownOpen(false); setKeywordSearch(''); }}
                className="px-3 py-1 bg-gray-700 border border-gray-600 rounded text-sm text-gray-200 hover:bg-gray-600 flex items-center space-x-1"
              >
                <span>Keyword</span>
                {keywordFilter.length > 0 && (
                  <span className="bg-cyan-600 text-white text-xs px-1.5 rounded">{keywordFilter.length}</span>
                )}
                <ChevronDownIcon className="h-4 w-4" />
              </button>
              {keywordDropdownOpen && (
                <div className="absolute z-10 mt-1 w-56 bg-gray-700 border border-gray-600 rounded-lg shadow-lg">
                  <div className="p-2 border-b border-gray-600">
                    <input
                      type="text"
                      value={keywordSearch}
                      onChange={(e) => setKeywordSearch(e.target.value)}
                      placeholder="Search keywords..."
                      className="w-full px-2 py-1 bg-gray-600 border border-gray-500 rounded text-sm text-gray-200 placeholder-gray-400 focus:outline-none"
                      autoFocus
                    />
                    {keywordFilter.length > 1 && (
                      <div className="flex items-center justify-between mt-2 text-xs">
                        <span className="text-gray-400">Match:</span>
                        <div className="flex rounded overflow-hidden">
                          <button
                            type="button"
                            onClick={() => setKeywordMatchMode('OR')}
                            className={`px-2 py-1 ${keywordMatchMode === 'OR' ? 'bg-cyan-600 text-white' : 'bg-gray-600 text-gray-300'}`}
                          >
                            OR
                          </button>
                          <button
                            type="button"
                            onClick={() => setKeywordMatchMode('AND')}
                            className={`px-2 py-1 ${keywordMatchMode === 'AND' ? 'bg-cyan-600 text-white' : 'bg-gray-600 text-gray-300'}`}
                          >
                            AND
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="max-h-48 overflow-y-auto">
                    {allKeywords.filter(kw => kw.toLowerCase().includes(keywordSearch.toLowerCase())).length === 0 ? (
                      <div className="px-3 py-2 text-gray-500 text-sm">No keywords found</div>
                    ) : (
                      allKeywords.filter(kw => kw.toLowerCase().includes(keywordSearch.toLowerCase())).map(kw => (
                        <label key={kw} className="flex items-center px-3 py-2 hover:bg-gray-600 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={keywordFilter.includes(kw)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setKeywordFilter([...keywordFilter, kw]);
                              } else {
                                setKeywordFilter(keywordFilter.filter(k => k !== kw));
                              }
                            }}
                            className="mr-2 rounded"
                          />
                          <span className="text-gray-200 text-sm">{kw}</span>
                        </label>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Abilities Multi-Select */}
            <div className="relative" ref={triggerDropdownRef}>
              <button
                type="button"
                onClick={() => { setTriggerDropdownOpen(!triggerDropdownOpen); setKeywordDropdownOpen(false); setTriggerSearch(''); }}
                className="px-3 py-1 bg-gray-700 border border-gray-600 rounded text-sm text-gray-200 hover:bg-gray-600 flex items-center space-x-1"
              >
                <span>Abilities</span>
                {triggerFilter.length > 0 && (
                  <span className="bg-purple-600 text-white text-xs px-1.5 rounded">{triggerFilter.length}</span>
                )}
                <ChevronDownIcon className="h-4 w-4" />
              </button>
              {triggerDropdownOpen && (
                <div className="absolute z-10 mt-1 w-56 bg-gray-700 border border-gray-600 rounded-lg shadow-lg">
                  <div className="p-2 border-b border-gray-600">
                    <input
                      type="text"
                      value={triggerSearch}
                      onChange={(e) => setTriggerSearch(e.target.value)}
                      placeholder="Search abilities..."
                      className="w-full px-2 py-1 bg-gray-600 border border-gray-500 rounded text-sm text-gray-200 placeholder-gray-400 focus:outline-none"
                      autoFocus
                    />
                    {triggerFilter.length > 1 && (
                      <div className="flex items-center justify-between mt-2 text-xs">
                        <span className="text-gray-400">Match:</span>
                        <div className="flex rounded overflow-hidden">
                          <button
                            type="button"
                            onClick={() => setTriggerMatchMode('OR')}
                            className={`px-2 py-1 ${triggerMatchMode === 'OR' ? 'bg-purple-600 text-white' : 'bg-gray-600 text-gray-300'}`}
                          >
                            OR
                          </button>
                          <button
                            type="button"
                            onClick={() => setTriggerMatchMode('AND')}
                            className={`px-2 py-1 ${triggerMatchMode === 'AND' ? 'bg-purple-600 text-white' : 'bg-gray-600 text-gray-300'}`}
                          >
                            AND
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="max-h-48 overflow-y-auto">
                    {availableTriggers.filter(t => t.toLowerCase().includes(triggerSearch.toLowerCase())).length === 0 ? (
                      <div className="px-3 py-2 text-gray-500 text-sm">No triggers found</div>
                    ) : (
                      availableTriggers.filter(t => t.toLowerCase().includes(triggerSearch.toLowerCase())).map(trig => (
                        <label key={trig} className="flex items-center px-3 py-2 hover:bg-gray-600 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={triggerFilter.includes(trig)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setTriggerFilter([...triggerFilter, trig]);
                              } else {
                                setTriggerFilter(triggerFilter.filter(t => t !== trig));
                              }
                            }}
                            className="mr-2 rounded"
                          />
                          <span className="text-gray-200 text-sm">{trig}</span>
                        </label>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {(keywordFilter.length > 0 || triggerFilter.length > 0) && (
              <button
                type="button"
                onClick={() => { setKeywordFilter([]); setTriggerFilter([]); setKeywordMatchMode('OR'); setTriggerMatchMode('OR'); }}
                className="px-3 py-1 bg-red-900/50 hover:bg-red-900 text-red-300 rounded text-sm flex items-center space-x-1"
              >
                <XMarkIcon className="h-4 w-4" />
                <span>Clear</span>
              </button>
            )}
          </div>
        </div>

        {/* Type Stats */}
        {groupBy !== 'none' && (
          <div className="flex flex-wrap gap-2">
            {effectiveGroupOrder.map(group => {
              const count = groupedCards[group]?.length || 0;
              if (count === 0) return null;
              return (
                <span key={group} className="px-3 py-1 bg-gray-800 rounded-full text-sm text-gray-400">
                  {getGroupLabel(group)}: <span className="text-gray-200">{count}</span>
                </span>
              );
            })}
          </div>
        )}

        {/* Cards Display */}
        {viewMode === 'list' ? (
          effectiveGroupOrder.map((group) => {
            const groupCards = groupedCards[group];
            if (!groupCards || groupCards.length === 0) return null;
            
            const isCollapsed = collapsedGroups.has(group);
            const totalQuantity = groupCards.reduce((sum, card) => sum + card.quantity, 0);

            return (
              <div key={group} className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-xl overflow-hidden">
                <button
                  type="button"
                  onClick={() => toggleGroup(group)}
                  className="w-full px-4 py-3 bg-gray-700/50 border-b border-gray-700/50 flex items-center justify-between hover:bg-gray-700/70 transition-colors"
                >
                  <h3 className="font-semibold text-gray-200 flex items-center space-x-2">
                    {isCollapsed ? (
                      <ChevronRightIcon className="h-5 w-5" />
                    ) : (
                      <ChevronDownIcon className="h-5 w-5" />
                    )}
                    <span>{getGroupLabel(group)}</span>
                    <span className="text-sm text-gray-500">({groupCards.length} unique, {totalQuantity} total)</span>
                  </h3>
                </button>
                
                {!isCollapsed && (
                  <div className="divide-y divide-gray-700/50">
                    {groupCards.map((card) => renderCard(card, false))}
                  </div>
                )}
              </div>
            );
          })
        ) : (
          // Grid View with collapsible groups
          <div className="space-y-6">
            {effectiveGroupOrder.map((group) => {
              const groupCards = groupedCards[group];
              if (!groupCards || groupCards.length === 0) return null;
              
              const isCollapsed = collapsedGroups.has(group);
              const totalQuantity = groupCards.reduce((sum, card) => sum + card.quantity, 0);
              
              return (
                <div key={group} className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-xl overflow-hidden">
                  <button
                    type="button"
                    onClick={() => toggleGroup(group)}
                    className="w-full px-4 py-3 bg-gray-700/50 border-b border-gray-700/50 flex items-center justify-between hover:bg-gray-700/70 transition-colors"
                  >
                    <h3 className="font-semibold text-gray-200 flex items-center space-x-2">
                      {isCollapsed ? (
                        <ChevronRightIcon className="h-5 w-5" />
                      ) : (
                        <ChevronDownIcon className="h-5 w-5" />
                      )}
                      <span>{getGroupLabel(group)}</span>
                      <span className="text-sm text-gray-500">({groupCards.length} unique, {totalQuantity} total)</span>
                    </h3>
                  </button>
                  
                  {!isCollapsed && (
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-4 xl:grid-cols-5 gap-4 p-4">
                      {groupCards.map((card) => renderGridCard(card))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {cards.length === 0 && (
          <div className="text-center py-12 bg-gray-800/30 rounded-xl">
            <p className="text-gray-500 text-lg">No cards in this deck yet</p>
            <p className="text-gray-600 text-sm mt-2">
              Use the Import List button or add cards individually
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CardList;
