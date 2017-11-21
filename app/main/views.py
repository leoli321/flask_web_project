# -*- coding: cp936 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app,make_response
from flask_login import login_required, current_user
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm
from .. import db
from ..models import Permission, Role, User, Post, Comment
from ..decorators import admin_required, permission_required

#�Լ����ɾ��post��������������index���ڸ���profileɾ�����ض���index.html��ôʵ�֣�ɾ����ֱ��ˢ���أ�
#ɾ��֮ǰӦ����ȷ�ϰ�ť��������Ӱ�
@main.route("/dele_post/<int:id>")
@login_required
def dele_post(id):
    post = Post.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    flash("The post has been deleted.")
    return redirect(url_for(".index"))


    
@main.route("/edit/<int:id>",methods=["GET","POST"])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)#get_or_404()����ָ��������Ӧ���У���û���ҵ�ָ��������������ֹ���󣬷���404������Ӧ
    if current_user != post.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash("The post has beeb updated.")
        return redirect(url_for(".post",id=post.id))
    form.body.data = post.body
    return render_template("edit_post.html",form=form)


@main.route("/post/<int:id>",methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        flash('Your comment has been published.')
        return redirect(url_for('.post',id=post.id,page=-1))
    page = int(request.args.get('page',1))
    if page == -1:
        page = (post.comments.count()-1)//\
               current_app.config['FLASKY_COMMENTS_PER_PAGE']+1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page,per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments=pagination.items
    return render_template("post.html",posts=[post],form=form,comments=comments,
                           pagination=pagination)


@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():
        post = Post(body=form.body.data,
                    author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('.index'))
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed',''))
    if show_followed:
        query=current_user.followed_posts #���ص���Post���������ԵĶ��󣬶�����ֵ
    else:
        query = Post.query
    #page = request.args.get('page', 1, type=int)
    #����ΪԴ��ʹ��11/2
    page = int(request.args.get("page",1))    
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts,show_followed=show_followed,
                           pagination=pagination)


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts,
                           pagination=pagination)



@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    #�����current_user��ôȥ��⣿��many_linking.md
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    #�ײ������user.email��Ϊcurren_userҲ���С�10/31
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)

#��user.html�е�Follow��ť��ת��������עĳ��
@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    #���˾��ã���follow��ת�����ģ��������if���û��Ҫ��
    if current_user.is_following(user):
        flash('You are already follow this user.')
        return redirect(url_for('.user',username=username))
    current_user.follow(user)
    flash('You are now following %s.' % username)
    return redirect(url_for('.user',username=username))

#��user.html�е�Unfollow��ť��ת������ȡ��
@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('You are not following this user.')
        return redirect(url_for('.user'),username=username)
    current_user.unfollow(user)
    flash('You are not following %s anymore' %username)
    return redirect(url_for('.user',username=username))

#��user.html�е�followers��ť��ת��������ʾ��ע�û����� followers of lengqian
@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page',1,type=int)
    pagination = user.followers.paginate(page,
                                         per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
                                         error_out=False)
    follows = [{'user':item.follower,'timestamp':item.timestamp}
               for item in pagination.items]
    return render_template("followers.html",user=user,title='Followers of',
                           endpoint='.followers',pagination=pagination,follows=follows)

#��user.html�е�followed��ť��ת��������ʾ�û���ע���� followed by lengqian
@main.route('/followed_by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page',1,type=int)
    pagination = user.followed.paginate(page,
                                         per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
                                         error_out=False)
    follows = [{'user':item.followed,'timestamp':item.timestamp}
               for item in pagination.items]
    return render_template("followers.html",user=user,title='Followed by',
                           endpoint='.followed_by',pagination=pagination,follows=follows)
    
@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed','',max_age=30*24*60*60)
    return resp

@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed','1',max_age=30*24*60*60)
    return resp


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page',1,type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page,per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'], error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments,pagination=pagination, page=page)
    

@main.route('/moderate/enable/<id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
        comment = Comment.query.get_or_404(id)
        comment.disabled = False
        db.session.add(comment)
        return redirect(url_for('.moderate',page=request.args.get('page',1,type=int)))


@main.route('/moderate/disable/<id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
        comment = Comment.query.get_or_404(id)
        comment.disabled = True
        db.session.add(comment)
        return redirect(url_for('.moderate', page=request.args.get('page',1,type=int)))

#�Լ���ӣ�����Աɾ�����۹���        
@main.route("/delete_comment/<int:id>")
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    db.session.delete(comment)
    db.session.commit()
    flash("The comment has been deleted.")
    return redirect(url_for(".moderate",page=request.args.get("page",1,type=int)))
