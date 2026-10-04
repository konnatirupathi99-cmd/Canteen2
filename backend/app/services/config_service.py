from app.models.configuration import Configuration
from sqlalchemy import or_

class ConfigService:
    @staticmethod
    def get_config(key, default=None, institution_id=None, campus_id=None, canteen_id=None, stall_id=None, product_id=None):
        """
        Resolves a configuration key deterministically using a hierarchy:
        1. Product
        2. Stall
        3. Canteen
        4. Campus
        5. Institution
        6. Global Default
        
        More specific configuration overrides broader configuration.
        """
        
        filters = []
        if product_id:
            filters.append(Configuration.product_id == product_id)
        if stall_id:
            filters.append(Configuration.stall_id == stall_id)
        if canteen_id:
            filters.append(Configuration.canteen_id == canteen_id)
        if campus_id:
            filters.append(Configuration.campus_id == campus_id)
        if institution_id:
            filters.append(Configuration.institution_id == institution_id)
            
        filters.append(Configuration.is_global == True)
        
        configs = Configuration.query.filter(
            Configuration.key == key,
            or_(*filters)
        ).all()
        
        if not configs:
            return default
            
        # Priority mapping: lower is higher priority
        priority_map = {
            'product': 1,
            'stall': 2,
            'canteen': 3,
            'campus': 4,
            'institution': 5,
            'global': 6
        }
        
        best_match = None
        best_priority = 999
        
        for cfg in configs:
            p = 999
            if cfg.product_id == product_id and product_id is not None:
                p = priority_map['product']
            elif cfg.stall_id == stall_id and stall_id is not None:
                p = priority_map['stall']
            elif cfg.canteen_id == canteen_id and canteen_id is not None:
                p = priority_map['canteen']
            elif cfg.campus_id == campus_id and campus_id is not None:
                p = priority_map['campus']
            elif cfg.institution_id == institution_id and institution_id is not None:
                p = priority_map['institution']
            elif cfg.is_global:
                p = priority_map['global']
                
            if p < best_priority:
                best_priority = p
                best_match = cfg
                
        if best_match:
            return best_match.value
            
        return default
        
    @staticmethod
    def set_config(key, value, is_global=False, institution_id=None, campus_id=None, canteen_id=None, stall_id=None, product_id=None, user_id=None):
        from app.extensions import db
        
        # Check if exactly this scope exists
        cfg = Configuration.query.filter_by(
            key=key,
            is_global=is_global,
            institution_id=institution_id,
            campus_id=campus_id,
            canteen_id=canteen_id,
            stall_id=stall_id,
            product_id=product_id
        ).first()
        
        if cfg:
            cfg.value = value
            cfg.updated_by = user_id
        else:
            cfg = Configuration(
                key=key,
                value=value,
                is_global=is_global,
                institution_id=institution_id,
                campus_id=campus_id,
                canteen_id=canteen_id,
                stall_id=stall_id,
                product_id=product_id,
                updated_by=user_id
            )
            db.session.add(cfg)
        
        db.session.commit()
        return cfg
