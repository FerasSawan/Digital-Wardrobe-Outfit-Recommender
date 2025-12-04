import { useState, useEffect } from 'react'
import './App.css'

const API_BASE_URL = "http://localhost:8000"
const CATEGORIES = ['shirt', 'pants', 'shorts', 'hoodie']

interface ClothingItem {
  id: number
  name: string | null
  image_path: string
  category: string
  created_at: string
  clothing_type?: string
  color?: string
  secondary_color?: string
  season?: string
  style?: string
  pattern?: string
  material?: string
  fit?: string
}

interface OutfitItem {
  item: ClothingItem
  reason: string
}

interface OutfitRecommendation {
  outfit: {
    top?: OutfitItem
    bottom?: OutfitItem
    additional?: OutfitItem[]
    description: string
    styling_tips: string
  }
  confidence: string
  metadata?: {
    model: string
    cost_usd: number
    tokens_used: number
    usage_stats?: {
      remaining_budget_usd: number
      monthly_cost_usd: number
    }
  }
}

function ConfirmationModal({ isOpen, onClose, onConfirm, itemName, itemCategory, itemImage }: {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  itemName: string | null;
  itemCategory: string;
  itemImage: string;
}) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h3 className="modal-title">Confirm Deletion</h3>
        <p className="modal-message">Are you sure you want to delete this item?</p>
        <div className="modal-item-preview">
          <img src={itemImage} alt={itemName || "Clothing Item"} />
          <div className="preview-details">
            <span className="preview-category">{itemCategory.charAt(0).toUpperCase() + itemCategory.slice(1)}</span>
            <p className="preview-name">{itemName || "Unnamed Item"}</p>
          </div>
        </div>
        <div className="modal-actions">
          <button className="modal-cancel-btn" onClick={onClose}>Cancel</button>
          <button className="modal-delete-btn" onClick={onConfirm}>Delete</button>
        </div>
      </div>
    </div>
  );
}

function EditCategoryModal({ isOpen, onClose, onSave, item, currentCategory }: {
  isOpen: boolean;
  onClose: () => void;
  onSave: (newCategory: string) => void;
  item: ClothingItem | null;
  currentCategory: string;
}) {
  const [selectedCategory, setSelectedCategory] = useState(currentCategory);

  useEffect(() => {
    setSelectedCategory(currentCategory);
  }, [currentCategory]);

  if (!isOpen || !item) return null;

  const getCategoryIcon = (cat: string) => {
    const icons: Record<string, string> = {
      shirt: '👔',
      pants: '👖',
      shorts: '🩳',
      hoodie: '🧥'
    }
    return icons[cat] || '👕'
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h3 className="modal-title">Change Category</h3>
        <p className="modal-message">Select a new category for "{item.name || 'Unnamed Item'}"</p>
        <div className="category-select-grid">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              className={`category-select-btn ${selectedCategory === cat ? 'active' : ''}`}
              onClick={() => setSelectedCategory(cat)}
            >
              <span className="category-icon">{getCategoryIcon(cat)}</span>
              {cat.charAt(0).toUpperCase() + cat.slice(1)}
            </button>
          ))}
        </div>
        <div className="modal-actions">
          <button className="modal-cancel-btn" onClick={onClose}>Cancel</button>
          <button className="modal-save-btn" onClick={() => onSave(selectedCategory)}>Save</button>
        </div>
      </div>
    </div>
  );
}

function BulkDeleteModal({ isOpen, onClose, onConfirm, count }: {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  count: number;
}) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h3 className="modal-title">Confirm Bulk Delete</h3>
        <p className="modal-message">Are you sure you want to delete {count} selected items?</p>
        <div className="modal-actions">
          <button className="modal-cancel-btn" onClick={onClose}>Cancel</button>
          <button className="modal-delete-btn" onClick={onConfirm}>Delete All</button>
        </div>
      </div>
    </div>
  );
}

function App() {
  const [activeTab, setActiveTab] = useState<'upload' | 'wardrobe' | 'outfits' | 'saved'>('upload')
  const [items, setItems] = useState<ClothingItem[]>([])
  const [name, setName] = useState("")
  const [files, setFiles] = useState<File[]>([])
  const [category, setCategory] = useState<string>(CATEGORIES[0])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState(false)
  const [newItemId, setNewItemId] = useState<number | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<ClothingItem | null>(null);
  
  // New state for advanced features
  const [selectMode, setSelectMode] = useState(false);
  const [selectedItems, setSelectedItems] = useState<Set<number>>(new Set());
  const [showEditModal, setShowEditModal] = useState(false);
  const [itemToEdit, setItemToEdit] = useState<ClothingItem | null>(null);
  const [showBulkDeleteModal, setShowBulkDeleteModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<'date' | 'name' | 'category'>('date');
  
  // Outfit generator state
  const [outfitRequest, setOutfitRequest] = useState("")
  const [outfitLoading, setOutfitLoading] = useState(false)
  const [outfitError, setOutfitError] = useState<string | null>(null)
  const [outfitRecommendation, setOutfitRecommendation] = useState<OutfitRecommendation | null>(null)
  const [selectedGender, setSelectedGender] = useState<'male' | 'female'>('female')
  const [savedOutfits, setSavedOutfits] = useState<any[]>([])
  const [savingOutfit, setSavingOutfit] = useState(false)

  useEffect(() => {
    fetchItems()
  }, [selectedCategory])

  useEffect(() => {
    if (activeTab === 'saved') {
      fetchSavedOutfits()
    }
  }, [activeTab])

  const fetchItems = async () => {
    try {
      const url = selectedCategory
        ? `${API_BASE_URL}/api/clothing-items/?category=${selectedCategory}`
        : `${API_BASE_URL}/api/clothing-items/`
      const response = await fetch(url)
      if (!response.ok) {
        throw new Error('Failed to fetch items')
      }
      const data = await response.json()
      setItems(data)
    } catch (err) {
      console.error('Error fetching items:', err)
      setError('Failed to load wardrobe items')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (files.length === 0) {
      setError('Please select at least one image file')
      return
    }
    if (!category) {
      setError('Please select a category')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const uploadPromises = files.map(async (file) => {
        const formData = new FormData()
        formData.append('file', file)
        if (name.trim()) {
          formData.append('name', name.trim())
        }
        formData.append('category', category)

        const response = await fetch(`${API_BASE_URL}/api/clothing-items/`, {
          method: 'POST',
          body: formData,
        })

        if (!response.ok) {
          throw new Error('Failed to upload item')
        }

        return await response.json()
      })

      const newItems = await Promise.all(uploadPromises)
      
      if (newItems.length > 0) {
        setNewItemId(newItems[0].id)
      }
      setSuccessMessage(true)

      setName("")
      setFiles([])
      const fileInput = document.getElementById('file-input') as HTMLInputElement
      if (fileInput) {
        fileInput.value = ''
      }

      await fetchItems()
      setTimeout(() => {
        setActiveTab('wardrobe')
        setTimeout(() => {
          setSuccessMessage(false)
          setNewItemId(null)
        }, 3000)
      }, 500)
    } catch (err) {
      console.error('Error uploading item:', err)
      setError('Failed to upload items. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const filesArray = Array.from(e.target.files);
      setFiles(filesArray);
    }
  }

  const confirmDelete = (item: ClothingItem) => {
    setItemToDelete(item);
    setShowDeleteModal(true);
  };

  const handleDelete = async () => {
    if (!itemToDelete) return;

    setShowDeleteModal(false);
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/clothing-items/${itemToDelete.id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete item');
      }

      setItems(items.filter(item => item.id !== itemToDelete.id));
      setItemToDelete(null);
    } catch (err) {
      console.error('Error deleting item:', err);
      setError('Failed to delete item. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleBulkDelete = async () => {
    setShowBulkDeleteModal(false);
    setLoading(true);
    setError(null);

    try {
      const deletePromises = Array.from(selectedItems).map(itemId =>
        fetch(`${API_BASE_URL}/api/clothing-items/${itemId}`, {
          method: 'DELETE',
        })
      );

      await Promise.all(deletePromises);
      
      setItems(items.filter(item => !selectedItems.has(item.id)));
      setSelectedItems(new Set());
      setSelectMode(false);
    } catch (err) {
      console.error('Error deleting items:', err);
      setError('Failed to delete some items. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleEditCategory = (item: ClothingItem) => {
    setItemToEdit(item);
    setShowEditModal(true);
  };

  const handleSaveCategory = async (newCategory: string) => {
    if (!itemToEdit) return;

    setShowEditModal(false);
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/clothing-items/${itemToEdit.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ category: newCategory }),
      });

      if (!response.ok) {
        throw new Error('Failed to update category');
      }

      const updatedItem = await response.json();
      setItems(items.map(item => item.id === updatedItem.id ? updatedItem : item));
      setItemToEdit(null);
    } catch (err) {
      console.error('Error updating category:', err);
      setError('Failed to update category. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const toggleSelectItem = (itemId: number) => {
    const newSelected = new Set(selectedItems);
    if (newSelected.has(itemId)) {
      newSelected.delete(itemId);
    } else {
      newSelected.add(itemId);
    }
    setSelectedItems(newSelected);
  };

  const toggleSelectAll = () => {
    if (selectedItems.size === filteredAndSortedItems.length) {
      setSelectedItems(new Set());
    } else {
      setSelectedItems(new Set(filteredAndSortedItems.map(item => item.id)));
    }
  };

  const handleGenerateOutfit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!outfitRequest.trim()) {
      setOutfitError('Please describe the outfit you want')
      return
    }

    setOutfitLoading(true)
    setOutfitError(null)
    setOutfitRecommendation(null)

    try {
      const response = await fetch(`${API_BASE_URL}/api/outfits/suggest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          request: outfitRequest.trim()
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to generate outfit')
      }

      const data = await response.json()
      setOutfitRecommendation(data)
    } catch (err: any) {
      console.error('Error generating outfit:', err)
      setOutfitError(err.message || 'Failed to generate outfit. Please try again.')
    } finally {
      setOutfitLoading(false)
    }
  };

  const handleSaveOutfit = async () => {
    if (!outfitRecommendation) return;

    setSavingOutfit(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/outfits/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          gender: selectedGender,
          original_request: outfitRequest,
          outfit: outfitRecommendation.outfit
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save outfit');
      }

      const data = await response.json();
      alert(`✨ Outfit saved as "${data.name}"!`);
      fetchSavedOutfits();
    } catch (err) {
      console.error('Error saving outfit:', err);
      alert('Failed to save outfit. Please try again.');
    } finally {
      setSavingOutfit(false);
    }
  };

  const fetchSavedOutfits = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/outfits/saved`);
      if (!response.ok) throw new Error('Failed to fetch saved outfits');
      const data = await response.json();
      setSavedOutfits(data);
    } catch (err) {
      console.error('Error fetching saved outfits:', err);
    }
  };

  const handleDeleteSavedOutfit = async (outfitId: number) => {
    if (!confirm('Delete this saved outfit?')) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/outfits/saved/${outfitId}`, {
        method: 'DELETE',
      });

      if (!response.ok) throw new Error('Failed to delete outfit');
      
      setSavedOutfits(savedOutfits.filter(o => o.id !== outfitId));
    } catch (err) {
      console.error('Error deleting outfit:', err);
      alert('Failed to delete outfit.');
    }
  };

  const getCategoryIcon = (cat: string) => {
    const icons: Record<string, string> = {
      shirt: '👔',
      pants: '👖',
      shorts: '🩳',
      hoodie: '🧥'
    }
    return icons[cat] || '👕'
  }

  const getCategoryName = (cat: string) => {
    return cat.charAt(0).toUpperCase() + cat.slice(1)
  }

  // Filter and sort items
  const filteredAndSortedItems = items
    .filter(item => {
      if (!searchQuery) return true;
      const query = searchQuery.toLowerCase();
      return (
        item.name?.toLowerCase().includes(query) ||
        item.category.toLowerCase().includes(query) ||
        item.clothing_type?.toLowerCase().includes(query) ||
        item.color?.toLowerCase().includes(query)
      );
    })
    .sort((a, b) => {
      if (sortBy === 'date') {
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      } else if (sortBy === 'name') {
        const nameA = a.name || 'Unnamed';
        const nameB = b.name || 'Unnamed';
        return nameA.localeCompare(nameB);
      } else if (sortBy === 'category') {
        return a.category.localeCompare(b.category);
      }
      return 0;
    });

  const itemsByCategory = filteredAndSortedItems.reduce((acc, item) => {
    if (!acc[item.category]) {
      acc[item.category] = []
    }
    acc[item.category].push(item)
    return acc
  }, {} as Record<string, ClothingItem[]>)

  return (
    <div className="app">
      <div className="particles-background"></div>
      <h1 className="main-title">
        Wardrobe
      </h1>

      <div className="tabs-container">
        <button
          className={`tab ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          <span className="tab-icon">📤</span>
          Upload
        </button>
        <button
          className={`tab ${activeTab === 'wardrobe' ? 'active' : ''}`}
          onClick={() => setActiveTab('wardrobe')}
        >
          <span className="tab-icon">👔</span>
          Wardrobe
        </button>
        <button
          className={`tab ${activeTab === 'outfits' ? 'active' : ''}`}
          onClick={() => setActiveTab('outfits')}
        >
          <span className="tab-icon">✨</span>
          Outfit Ideas
        </button>
        <button
          className={`tab ${activeTab === 'saved' ? 'active' : ''}`}
          onClick={() => setActiveTab('saved')}
        >
          <span className="tab-icon">💾</span>
          Saved Outfits
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'upload' && (
          <div className="upload-section">
            <h2>Upload Clothing Items</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="name">Name (optional)</label>
                <input
                  type="text"
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., Blue Jeans"
                />
              </div>

              <div className="form-group">
                <label htmlFor="category">Category *</label>
                <div className="category-buttons">
                  {CATEGORIES.map((cat) => (
                    <button
                      key={cat}
                      type="button"
                      className={`category-btn ${category === cat ? 'active' : ''}`}
                      onClick={() => setCategory(cat)}
                    >
                      <span className="category-icon">{getCategoryIcon(cat)}</span>
                      {getCategoryName(cat)}
                    </button>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="file-input">Choose images (multiple allowed)</label>
                <input
                  type="file"
                  id="file-input"
                  accept="image/*"
                  multiple
                  onChange={handleFileChange}
                />
                {files.length > 0 && (
                  <p className="file-count">{files.length} file(s) selected</p>
                )}
              </div>

              <button type="submit" disabled={loading || files.length === 0 || !category} className="upload-btn">
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    Uploading...
                  </>
                ) : (
                  <>
                    <span>⚡</span> Upload {files.length > 1 ? `${files.length} Items` : 'Item'}
                  </>
                )}
              </button>

              {error && <div className="error">{error}</div>}
              {successMessage && (
                <div className="success-message">
                  <span className="success-icon">✨</span>
                  <span>{files.length > 1 ? 'Items' : 'Item'} uploaded successfully!</span>
                </div>
              )}
            </form>
          </div>
        )}

        {activeTab === 'wardrobe' && (
          <div className="wardrobe-section">
            <div className="wardrobe-header">
              <h2>
                My Wardrobe
                <span className="item-count">{filteredAndSortedItems.length} items</span>
              </h2>
              
              <div className="wardrobe-controls">
                <input
                  type="text"
                  className="search-input"
                  placeholder="🔍 Search items..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                
                <select 
                  className="sort-select"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as 'date' | 'name' | 'category')}
                >
                  <option value="date">Sort by Date</option>
                  <option value="name">Sort by Name</option>
                  <option value="category">Sort by Category</option>
                </select>

                <button
                  className={`select-mode-btn ${selectMode ? 'active' : ''}`}
                  onClick={() => {
                    setSelectMode(!selectMode);
                    if (selectMode) setSelectedItems(new Set());
                  }}
                >
                  {selectMode ? '✓ Done' : '☑️ Select'}
                </button>

                {selectMode && selectedItems.size > 0 && (
                  <button
                    className="bulk-delete-btn"
                    onClick={() => setShowBulkDeleteModal(true)}
                  >
                    🗑️ Delete ({selectedItems.size})
                  </button>
                )}
              </div>

              <div className="category-filters">
                <button
                  className={`category-filter ${selectedCategory === null ? 'active' : ''}`}
                  onClick={() => setSelectedCategory(null)}
                >
                  All ({items.length})
                </button>
                {CATEGORIES.map((cat) => (
                  <button
                    key={cat}
                    className={`category-filter ${selectedCategory === cat ? 'active' : ''}`}
                    onClick={() => setSelectedCategory(cat)}
                  >
                    {getCategoryIcon(cat)} {getCategoryName(cat)} ({itemsByCategory[cat]?.length || 0})
                  </button>
                ))}
              </div>

              {selectMode && (
                <div className="select-all-container">
                  <button className="select-all-btn" onClick={toggleSelectAll}>
                    {selectedItems.size === filteredAndSortedItems.length ? 'Deselect All' : 'Select All'}
                  </button>
                </div>
              )}
            </div>

            {filteredAndSortedItems.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">👕</div>
                <p>{searchQuery ? 'No items match your search.' : 'No items yet. Upload your first clothing item!'}</p>
              </div>
            ) : (
              <div className="wardrobe-grid">
                {filteredAndSortedItems.map((item, index) => (
                  <div
                    key={item.id}
                    className={`wardrobe-item ${newItemId === item.id ? 'new-item' : ''} ${selectedItems.has(item.id) ? 'selected' : ''}`}
                    style={{ animationDelay: `${index * 0.1}s` }}
                    onClick={() => selectMode && toggleSelectItem(item.id)}
                  >
                    {selectMode && (
                      <div className="select-checkbox">
                        <input
                          type="checkbox"
                          checked={selectedItems.has(item.id)}
                          onChange={() => toggleSelectItem(item.id)}
                        />
                      </div>
                    )}
                    <div className="item-image-wrapper">
                      <img
                        src={`${API_BASE_URL}/${item.image_path}`}
                        alt={item.name || 'Clothing item'}
                        onError={(e) => {
                          (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200"%3E%3Crect width="200" height="200" fill="%23ddd"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23999"%3EImage not found%3C/text%3E%3C/svg%3E'
                        }}
                      />
                      <div className="item-overlay"></div>
                      {!selectMode && (
                        <>
                          <button
                            className="edit-btn"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleEditCategory(item);
                            }}
                            disabled={loading}
                          >
                            ✏️
                          </button>
                          <button
                            className="delete-btn"
                            onClick={(e) => {
                              e.stopPropagation();
                              confirmDelete(item);
                            }}
                            disabled={loading}
                          >
                            🗑️
                          </button>
                        </>
                      )}
                    </div>
                    <div className="item-info">
                      <span className="item-category-badge">
                        {getCategoryIcon(item.category)} {getCategoryName(item.category)}
                      </span>
                      {item.name && <div className="item-name">{item.name}</div>}
                      <div className="item-date">
                        {new Date(item.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'outfits' && (
          <div className="outfits-section">
            <h2>✨ Outfit Ideas</h2>
            <p className="outfit-subtitle">Tell me what you're looking for, and I'll help you pick the perfect outfit!</p>
            
            <form onSubmit={handleGenerateOutfit} className="outfit-form">
              <div className="form-group">
                <label>Select Your Style</label>
                <div className="gender-selector">
                  <button
                    type="button"
                    className={`gender-btn ${selectedGender === 'female' ? 'active' : ''}`}
                    onClick={() => setSelectedGender('female')}
                  >
                    <span className="gender-icon">👩</span>
                    Women's
                  </button>
                  <button
                    type="button"
                    className={`gender-btn ${selectedGender === 'male' ? 'active' : ''}`}
                    onClick={() => setSelectedGender('male')}
                  >
                    <span className="gender-icon">👨</span>
                    Men's
                  </button>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="outfit-request">What outfit do you need?</label>
                <input
                  type="text"
                  id="outfit-request"
                  value={outfitRequest}
                  onChange={(e) => setOutfitRequest(e.target.value)}
                  placeholder="e.g., casual summer day outfit, formal business meeting, coffee date..."
                  className="outfit-input"
                />
              </div>

              <button type="submit" disabled={outfitLoading || !outfitRequest.trim()} className="generate-btn">
                {outfitLoading ? (
                  <>
                    <span className="spinner"></span>
                    Finding your outfit...
                  </>
                ) : (
                  <>
                    <span>✨</span> Find My Outfit
                  </>
                )}
              </button>

              {outfitError && <div className="error">{outfitError}</div>}
            </form>

            {outfitRecommendation && (
              <div className="outfit-result">
                <div className="outfit-header">
                  <h3>👔 Here's What I Picked</h3>
                </div>

                <div className="mannequin-display">
                  <div className={`mannequin-container ${selectedGender}-mannequin`}>
                    <img 
                      src={`/mannequins/${selectedGender}.png`}
                      alt={`${selectedGender} mannequin`}
                      className="mannequin-body"
                    />
                    
                    {outfitRecommendation.outfit.top && (
                      <div className={`clothing-overlay top-position ${outfitRecommendation.outfit.top.item.category}-overlay ${selectedGender}-top`}>
                        <img 
                          src={`${API_BASE_URL}/${outfitRecommendation.outfit.top.item.image_path}`}
                          alt={outfitRecommendation.outfit.top.item.name || 'Top'}
                          className="clothing-item-overlay"
                        />
                      </div>
                    )}
                    
                    {outfitRecommendation.outfit.bottom && (
                      <div className={`clothing-overlay bottom-position ${outfitRecommendation.outfit.bottom.item.category}-overlay ${selectedGender}-bottom`}>
                        <img 
                          src={`${API_BASE_URL}/${outfitRecommendation.outfit.bottom.item.image_path}`}
                          alt={outfitRecommendation.outfit.bottom.item.name || 'Bottom'}
                          className="clothing-item-overlay"
                        />
                      </div>
                    )}
                  </div>

                  <div className="outfit-details-panel">
                    <div className="outfit-items-list">
                      {outfitRecommendation.outfit.top && (
                        <div className="outfit-item-detail">
                          <div className="item-thumbnail">
                            <img 
                              src={`${API_BASE_URL}/${outfitRecommendation.outfit.top.item.image_path}`}
                              alt={outfitRecommendation.outfit.top.item.name || 'Top'}
                            />
                          </div>
                          <div className="item-info-detail">
                            <span className="item-label">👕 TOP</span>
                            <h4>{outfitRecommendation.outfit.top.item.name || 'Unnamed'}</h4>
                            <p className="item-reason">{outfitRecommendation.outfit.top.reason}</p>
                            <div className="item-tags">
                              {outfitRecommendation.outfit.top.item.color && (
                                <span className="item-tag">🎨 {outfitRecommendation.outfit.top.item.color}</span>
                              )}
                              {outfitRecommendation.outfit.top.item.style && (
                                <span className="item-tag">✨ {outfitRecommendation.outfit.top.item.style}</span>
                              )}
                            </div>
                          </div>
                        </div>
                      )}

                      {outfitRecommendation.outfit.bottom && (
                        <div className="outfit-item-detail">
                          <div className="item-thumbnail">
                            <img 
                              src={`${API_BASE_URL}/${outfitRecommendation.outfit.bottom.item.image_path}`}
                              alt={outfitRecommendation.outfit.bottom.item.name || 'Bottom'}
                            />
                          </div>
                          <div className="item-info-detail">
                            <span className="item-label">👖 BOTTOM</span>
                            <h4>{outfitRecommendation.outfit.bottom.item.name || 'Unnamed'}</h4>
                            <p className="item-reason">{outfitRecommendation.outfit.bottom.reason}</p>
                            <div className="item-tags">
                              {outfitRecommendation.outfit.bottom.item.color && (
                                <span className="item-tag">🎨 {outfitRecommendation.outfit.bottom.item.color}</span>
                              )}
                              {outfitRecommendation.outfit.bottom.item.style && (
                                <span className="item-tag">✨ {outfitRecommendation.outfit.bottom.item.style}</span>
                              )}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    {outfitRecommendation.outfit.description && (
                      <div className="outfit-description">
                        <p>{outfitRecommendation.outfit.description}</p>
                      </div>
                    )}

                    <button
                      className="save-outfit-btn"
                      onClick={handleSaveOutfit}
                      disabled={savingOutfit}
                    >
                      {savingOutfit ? (
                        <>
                          <span className="spinner"></span>
                          Saving...
                        </>
                      ) : (
                        <>
                          <span>💾</span> Save This Outfit
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {!outfitRecommendation && !outfitLoading && (
              <div className="outfit-suggestions">
                <h4>💭 Need ideas? Try these:</h4>
                <div className="suggestion-chips">
                  <button onClick={() => setOutfitRequest("casual summer day outfit")} className="suggestion-chip">
                    ☀️ Summer Day
                  </button>
                  <button onClick={() => setOutfitRequest("formal business meeting")} className="suggestion-chip">
                    💼 Work Meeting
                  </button>
                  <button onClick={() => setOutfitRequest("comfortable coffee date look")} className="suggestion-chip">
                    ☕ Coffee Date
                  </button>
                  <button onClick={() => setOutfitRequest("workout gym outfit")} className="suggestion-chip">
                    💪 Gym
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'saved' && (
          <div className="saved-outfits-section">
            <h2>💾 Saved Outfits</h2>
            <p className="outfit-subtitle">Your favorite outfit combinations</p>

            {savedOutfits.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">💾</div>
                <p>No saved outfits yet. Generate and save your first outfit!</p>
              </div>
            ) : (
              <div className="saved-outfits-grid">
                {savedOutfits.map((outfit) => (
                  <div key={outfit.id} className="saved-outfit-card">
                    <div className="saved-outfit-header">
                      <h3>{outfit.name}</h3>
                      <span className="gender-badge">{outfit.gender === 'female' ? '👩' : '👨'}</span>
                    </div>
                    
                    {outfit.description && (
                      <p className="saved-outfit-description">{outfit.description}</p>
                    )}

                    <div className="saved-outfit-items">
                      {outfit.outfit_data?.outfit?.top && (
                        <div className="saved-item-preview">
                          <img 
                            src={`${API_BASE_URL}/${outfit.outfit_data.outfit.top.item.image_path}`}
                            alt="Top"
                          />
                          <span className="item-badge">👕</span>
                        </div>
                      )}
                      {outfit.outfit_data?.outfit?.bottom && (
                        <div className="saved-item-preview">
                          <img 
                            src={`${API_BASE_URL}/${outfit.outfit_data.outfit.bottom.item.image_path}`}
                            alt="Bottom"
                          />
                          <span className="item-badge">👖</span>
                        </div>
                      )}
                    </div>

                    <div className="saved-outfit-footer">
                      <span className="saved-date">
                        {new Date(outfit.created_at).toLocaleDateString()}
                      </span>
                      <button
                        className="delete-saved-btn"
                        onClick={() => handleDeleteSavedOutfit(outfit.id)}
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {itemToDelete && (
        <ConfirmationModal
          isOpen={showDeleteModal}
          onClose={() => setShowDeleteModal(false)}
          onConfirm={handleDelete}
          itemName={itemToDelete.name}
          itemCategory={getCategoryName(itemToDelete.category)}
          itemImage={`${API_BASE_URL}/${itemToDelete.image_path}`}
        />
      )}

      {itemToEdit && (
        <EditCategoryModal
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
          onSave={handleSaveCategory}
          item={itemToEdit}
          currentCategory={itemToEdit.category}
        />
      )}

      <BulkDeleteModal
        isOpen={showBulkDeleteModal}
        onClose={() => setShowBulkDeleteModal(false)}
        onConfirm={handleBulkDelete}
        count={selectedItems.size}
      />
    </div>
  )
}

export default App
