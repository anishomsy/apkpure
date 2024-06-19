from apkpure.apkpure import ApkPure
from flask import flash, redirect

class SearchService:
    def __init__(self, query) -> None:
        self.query = query
        self.api = ApkPure()
    def search(self):
        
        try:
            results = self.api.search_all(self.query)
        except:
            flash('App not found')
            return redirect('homepage')
        
        if results:
            return results
        return False
        
        