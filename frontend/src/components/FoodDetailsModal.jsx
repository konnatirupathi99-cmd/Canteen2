import React, { useState, useEffect } from 'react';
import { X, Star, Clock, Info, CheckCircle2, AlertTriangle, Loader2 } from 'lucide-react';
import { foodService } from '../services/foodService';
import { authService } from '../services/authService';
import './FoodDetailsModal.css';

export default function FoodDetailsModal({ food, onClose, onAddToCart }) {
  const [activeImage, setActiveImage] = useState(food.images && food.images.length > 0 ? food.images[0] : food.image);
  const [reviews, setReviews] = useState([]);
  const [loadingReviews, setLoadingReviews] = useState(true);
  
  const [newReview, setNewReview] = useState({ rating: 0, comment: '' });
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewSuccess, setReviewSuccess] = useState(false);
  
  const currentUser = authService.getCurrentUser();

  useEffect(() => {
    const fetchReviews = async () => {
      try {
        const data = await foodService.getReviews(food.id);
        setReviews(data);
      } catch (err) {
        console.error("Failed to load reviews");
      } finally {
        setLoadingReviews(false);
      }
    };
    fetchReviews();
  }, [food.id]);

  const handleStarClick = (rating) => {
    setNewReview(prev => ({ ...prev, rating }));
  };

  const submitReview = async (e) => {
    e.preventDefault();
    if (newReview.rating === 0) return;
    
    setSubmittingReview(true);
    try {
      const added = await foodService.addReview(food.id, {
        userId: currentUser?.id,
        userName: currentUser?.name || 'Anonymous',
        rating: newReview.rating,
        comment: newReview.comment
      });
      setReviews([added, ...reviews]);
      setReviewSuccess(true);
      setNewReview({ rating: 0, comment: '' });
      setTimeout(() => setReviewSuccess(false), 3000);
    } catch (err) {
      console.error(err);
    } finally {
      setSubmittingReview(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content food-details-modal" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}><X size={24}/></button>
        
        <div className="food-details-grid">
          {/* Left Column: Visuals */}
          <div className="food-details-visuals">
            <div className="main-image-container">
              {food.popular && <div className="badge-popular">🔥 POPULAR</div>}
              {food.rating >= 4.5 && <div className="badge-top-rated">★ TOP RATED</div>}
              <img src={activeImage || 'https://via.placeholder.com/800?text=No+Image'} alt={food.name} className="main-image" />
            </div>
            
            {food.images && food.images.length > 1 && (
              <div className="image-gallery">
                {food.images.map((img, idx) => (
                  <img 
                    key={idx} 
                    src={img} 
                    alt={`${food.name} ${idx+1}`} 
                    className={`gallery-thumbnail ${activeImage === img ? 'active' : ''}`}
                    onClick={() => setActiveImage(img)}
                  />
                ))}
              </div>
            )}
          </div>
          
          {/* Right Column: Info & Reviews */}
          <div className="food-details-info">
            <div className="food-header">
              <div className="flex justify-between items-start">
                <h2>{food.name}</h2>
                <div className="food-price-large">₹{food.price}</div>
              </div>
              <div className="flex items-center gap-4 mt-2">
                <div className="food-rating">
                  <Star size={16} fill="var(--warning)" color="var(--warning)" />
                  <span className="font-bold ml-1">{food.rating > 0 ? food.rating.toFixed(1) : 'New'}</span>
                  <span className="text-secondary text-sm ml-1">({food.reviewCount || 0} Reviews)</span>
                </div>
                <div className="food-prep">
                  <Clock size={14}/> {food.preparationTime}
                </div>
                <div>
                  {food.vegStatus === 'VEG' ? (
                    <span className="text-success text-sm font-bold border border-success px-2 py-0.5 rounded-full">● VEG</span>
                  ) : (
                    <span className="text-danger text-sm font-bold border border-danger px-2 py-0.5 rounded-full">▲ NON-VEG</span>
                  )}
                </div>
              </div>
            </div>

            <div className="food-action-box my-6">
              <div className="flex justify-between items-center mb-4">
                <div className="status">
                  {food.isAvailable ? (
                    <span className={`status-badge ${food.stock <= (food.lowStockThreshold || 10) ? 'text-warning bg-warning-light' : 'text-success bg-success-light'}`}>
                      {food.stock <= (food.lowStockThreshold || 10) ? `⚠ Only ${food.stock} left` : '● AVAILABLE'}
                    </span>
                  ) : (
                    <span className="status-badge text-danger bg-danger-light">OUT OF STOCK</span>
                  )}
                </div>
                <div className="text-sm text-secondary">
                  Stall: <strong>{food.stall}</strong>
                </div>
              </div>
              <button 
                className={`btn w-full btn-large ${food.isAvailable ? 'btn-primary' : 'btn-disabled'}`}
                onClick={() => {
                  if (food.isAvailable) {
                    onAddToCart(food);
                    onClose();
                  }
                }}
                disabled={!food.isAvailable}
              >
                {food.isAvailable ? '+ ADD TO CART' : 'CURRENTLY UNAVAILABLE'}
              </button>
            </div>

            <div className="food-description mb-6">
              <h3 className="section-subtitle">About this item</h3>
              <p>{food.description || 'No description available.'}</p>
              
              {(food.ingredients || food.allergens) && (
                <div className="food-meta-info mt-4">
                  {food.ingredients && (
                    <div className="mb-2">
                      <strong>Ingredients:</strong> {food.ingredients.join(', ')}
                    </div>
                  )}
                  {food.allergens && (
                    <div className="text-warning-dark">
                      <AlertTriangle size={14} className="inline mr-1" />
                      <strong>Allergens:</strong> {food.allergens.join(', ')}
                    </div>
                  )}
                  {food.servingInfo && (
                    <div className="mt-2 text-sm text-secondary">
                      <Info size={14} className="inline mr-1" />
                      Serving: {food.servingInfo}
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="reviews-section">
              <h3 className="section-subtitle flex items-center justify-between border-b pb-2 mb-4">
                Customer Reviews
                <span className="text-sm font-normal text-secondary">{reviews.length} Ratings</span>
              </h3>
              
              {/* Review Input Box (for authenticated users) */}
              {currentUser && (
                <div className="review-composer mb-6 p-4 bg-background rounded-lg border">
                  <h4 className="text-sm font-bold mb-2">Rate this food</h4>
                  <div className="flex gap-1 mb-3">
                    {[1,2,3,4,5].map(star => (
                      <Star 
                        key={star} 
                        size={24} 
                        fill={star <= newReview.rating ? 'var(--warning)' : 'none'} 
                        color={star <= newReview.rating ? 'var(--warning)' : 'var(--border)'}
                        className="cursor-pointer transition-transform hover:scale-110"
                        onClick={() => handleStarClick(star)}
                      />
                    ))}
                  </div>
                  {newReview.rating > 0 && (
                    <form onSubmit={submitReview}>
                      <textarea 
                        className="input-field w-full mb-3" 
                        rows="3" 
                        placeholder="Write your review here (optional)..."
                        value={newReview.comment}
                        onChange={(e) => setNewReview({...newReview, comment: e.target.value})}
                      />
                      <button type="submit" className="btn btn-primary" disabled={submittingReview}>
                        {submittingReview ? <Loader2 size={16} className="spin inline mr-2"/> : null}
                        SUBMIT REVIEW
                      </button>
                    </form>
                  )}
                  {reviewSuccess && (
                    <div className="text-success text-sm mt-2 flex items-center">
                      <CheckCircle2 size={16} className="mr-1"/> Thank you for your review!
                    </div>
                  )}
                </div>
              )}

              {loadingReviews ? (
                <div className="flex justify-center p-8"><Loader2 className="spin text-primary" /></div>
              ) : reviews.length === 0 ? (
                <div className="text-center p-6 text-secondary bg-background rounded-lg">
                  No customer reviews yet. Be the first to review!
                </div>
              ) : (
                <div className="reviews-list space-y-4">
                  {reviews.map(review => (
                    <div key={review.id} className="review-card p-4 border rounded-lg">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <div className="font-bold">{review.userName}</div>
                          <div className="text-xs text-success flex items-center">
                            <CheckCircle2 size={12} className="mr-1"/> Verified Order
                          </div>
                        </div>
                        <div className="text-xs text-secondary">
                          {new Date(review.createdAt).toLocaleDateString()}
                        </div>
                      </div>
                      <div className="flex mb-2">
                        {[...Array(5)].map((_, i) => (
                          <Star key={i} size={14} fill={i < review.rating ? 'var(--warning)' : 'none'} color={i < review.rating ? 'var(--warning)' : 'var(--border)'} />
                        ))}
                      </div>
                      {review.comment && <p className="text-sm text-dark mt-2">{review.comment}</p>}
                      
                      {review.managerResponse && (
                        <div className="mt-3 p-3 bg-background rounded text-sm border-l-2 border-primary">
                          <strong className="text-xs text-secondary uppercase block mb-1">Manager Response</strong>
                          {review.managerResponse}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}
